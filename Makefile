# libazahar-py host: build/libazhost.dylib (the azh_* API) and build/azhost (the thin CLI over it).
CC = clang
CFLAGS = -std=c11 -O2 -g -Wall -Wextra -Werror -Wshadow -Wstrict-prototypes -Wmissing-prototypes \
         -isystem vendor -isystem vendor/include -Ihost
LIB_SRC = $(filter-out host/azhost_main.c,$(wildcard host/*.c))
LIB_OBJ = $(patsubst host/%.c,build/obj/%.o,$(LIB_SRC))
HEADERS = $(wildcard host/*.h) Makefile

all: build/libazhost.dylib build/azhost

build/obj/%.o: host/%.c $(HEADERS)
	@mkdir -p build/obj
	$(CC) $(CFLAGS) -c -o $@ $<

build/libazhost.dylib: $(LIB_OBJ) host/libazhost.exports
	$(CC) -dynamiclib -install_name @rpath/libazhost.dylib -Wl,-exported_symbols_list,host/libazhost.exports \
	    -o $@ $(LIB_OBJ) -lz -lpthread

# azhost links sdcopy.o, profile.o, input.o and msg.o directly: azh__copy_tree, azh__profile_*, azh__script_line and
# azh__print_escaped are internal, not exported symbols of the library
build/azhost: build/obj/azhost_main.o build/obj/sdcopy.o build/obj/profile.o build/obj/input.o build/obj/msg.o build/libazhost.dylib
	$(CC) -o $@ build/obj/azhost_main.o build/obj/sdcopy.o build/obj/profile.o build/obj/input.o build/obj/msg.o -lm -Lbuild -lazhost -Wl,-rpath,@loader_path

# static analysis: one pass per host source, no .plist output
check:
	tools/check-obinary.sh
	@for f in host/*.c; do \
	    echo "analyze $$f"; \
	    clang --analyze -Xclang -analyzer-werror -Xanalyzer -analyzer-output=text $(CFLAGS) -o /dev/null $$f || exit 1; \
	done

test-version: build/test-version
	build/test-version

build/test-version: tests/test_version.c host/version.c $(HEADERS)
	@mkdir -p build
	$(CC) $(CFLAGS) -o $@ tests/test_version.c host/version.c

# step B's test app lives in testapp/ with its own Makefile
testapp:
	$(MAKE) -C testapp

# step C's pure-C unit tests: no core, no Vulkan. -ffp-contract=off keeps the float32 touch model exact.
TEST_SRC = host/input.c host/match.c host/msg.c host/rawcopy.c host/crop.c host/png.c host/sdcopy.c host/statemeta.c host/watch.c host/profile.c \
           $(wildcard tests/host/*.c)

test-host: build/test-host
	build/test-host

build/test-host: $(TEST_SRC) $(HEADERS) $(wildcard tests/host/*.h)
	@mkdir -p build
	$(CC) $(CFLAGS) -ffp-contract=off -Itests/host -o $@ $(TEST_SRC) -lz -lm

clean:
	rm -rf build/libazhost.dylib build/azhost build/test-version build/test-host build/obj

.PHONY: all check test-version test-host testapp clean win64 test-version-win test-host-win check-obinary

# Windows host (branch port-win, mingw-w64 posix threads): libazhost.dll, azhost.exe, test-host.exe, test-version.exe.
#   make win64 [ZLIB_PREFIX=<prefix of a mingw-built zlib>]
#   make test-host-win test-version-win   (run the two test programs; they need Windows or wine)
# The DLL exports what host/libazhost.exports lists (the leading underscore of the Mach-O list dropped into a .def).
# azhost.exe links the DLL, and links win_sdcopy.o, profile.o, input.o and msg.o directly, as azhost does on the Mac.
WIN_CC ?= x86_64-w64-mingw32-gcc-posix
ZLIB_PREFIX ?= $(HOME)/3ds/zlib-mingw
WIN_DIR = build/win64
WIN_PLAT = host/plat/win_compat.c host/plat/win_sdcopy.c
WIN_LIB_SRC = $(filter-out host/azhost_main.c host/sdcopy.c,$(wildcard host/*.c)) $(WIN_PLAT)
WIN_CFLAGS = -std=gnu11 -D__USE_MINGW_ANSI_STDIO=1 -D_FILE_OFFSET_BITS=64 -O2 -g -Wall -Wextra -Werror -Wshadow -Wstrict-prototypes -Wmissing-prototypes \
             -isystem vendor -isystem vendor/include -isystem $(ZLIB_PREFIX)/include -Ihost -Ihost/plat
WIN_LDFLAGS = -static -static-libgcc -L$(ZLIB_PREFIX)/lib
WIN_HEADERS = $(HEADERS) $(wildcard host/plat/*.h)

win64: $(WIN_DIR)/libazhost.dll $(WIN_DIR)/azhost.exe $(WIN_DIR)/test-host.exe $(WIN_DIR)/test-version.exe

$(WIN_DIR)/libazhost.def: host/libazhost.exports
	@mkdir -p $(WIN_DIR)
	(echo EXPORTS; sed 's/^_//' host/libazhost.exports) > $@

$(WIN_DIR)/libazhost.dll: $(WIN_LIB_SRC) $(WIN_HEADERS) $(WIN_DIR)/libazhost.def
	$(WIN_CC) $(WIN_CFLAGS) -shared -o $@ $(WIN_LIB_SRC) $(WIN_DIR)/libazhost.def -Wl,--out-implib,$(WIN_DIR)/libazhost.a \
	    $(WIN_LDFLAGS) -lz -lpsapi -lbcrypt -lm

$(WIN_DIR)/azhost.exe: host/azhost_main.c host/profile.c host/input.c host/msg.c $(WIN_PLAT) $(WIN_DIR)/libazhost.dll $(WIN_HEADERS)
	$(WIN_CC) $(WIN_CFLAGS) -o $@ host/azhost_main.c host/profile.c host/input.c host/msg.c $(WIN_PLAT) \
	    $(WIN_LDFLAGS) -L$(WIN_DIR) -lazhost -lpsapi -lbcrypt -lm

$(WIN_DIR)/test-version.exe: tests/test_version.c host/version.c $(WIN_HEADERS)
	@mkdir -p $(WIN_DIR)
	$(WIN_CC) $(WIN_CFLAGS) -o $@ tests/test_version.c host/version.c $(WIN_LDFLAGS)

WIN_TEST_SRC = host/input.c host/match.c host/msg.c host/rawcopy.c host/crop.c host/png.c host/statemeta.c host/watch.c \
               host/profile.c $(WIN_PLAT) $(wildcard tests/host/*.c)

$(WIN_DIR)/test-host.exe: $(WIN_TEST_SRC) $(WIN_HEADERS) $(wildcard tests/host/*.h)
	@mkdir -p $(WIN_DIR)
	$(WIN_CC) $(WIN_CFLAGS) -ffp-contract=off -Itests/host -o $@ $(WIN_TEST_SRC) $(WIN_LDFLAGS) -lz -lpsapi -lbcrypt -lm

# Windows only: the make rules above are cross builds; these run the exes where they can run (the PC's WSL runs .exe)
test-version-win: $(WIN_DIR)/test-version.exe
	$(WIN_DIR)/test-version.exe

check-obinary:
	tools/check-obinary.sh

test-host-win: check-obinary $(WIN_DIR)/test-host.exe
	$(WIN_DIR)/test-host.exe
