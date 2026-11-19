# libazahar-py host. On macOS (HOST_OS Darwin): build/libazhost.dylib (the azh_* API) and build/azhost (the thin CLI over
# it). On Windows, in an MSYS2 MINGW64 shell: build/libazhost.dll and build/azhost.exe (the second half of this file).
# HOST_OS comes from uname; `make HOST_OS=Darwin ...` forces the macOS half.
HOST_OS ?= $(shell uname -s)

ifeq ($(HOST_OS),Darwin)

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

testapp-tone:
	$(MAKE) -C testapp-tone

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

.PHONY: all check test-version test-host testapp testapp-tone clean win64 test-version-win test-host-win check-obinary

else

# Windows host (mingw-w64): build/libazhost.dll, build/azhost.exe, and the two test programs build/test-host.exe and
# build/test-version.exe. Objects are not kept; the export .def and the import library go to build/win64/.
#   make                   libazhost.dll and azhost.exe
#   make win64             those two plus test-host.exe and test-version.exe
#   make check             check-obinary, then the clang analysis of every host source (needs mingw-w64-x86_64-clang)
#   make test-host test-version   build and run the two test programs
# Build in the MINGW64 shell of MSYS2 (gcc, make, zlib from the mingw-w64-x86_64 packages). The other MSYS2 shells link
# other runtimes and are refused. A cross build (WSL, Linux) sets WIN_CC and ZLIB_PREFIX on the command line.
ifneq ($(MSYSTEM),)
ifneq ($(MSYSTEM),MINGW64)
$(error this Makefile builds in the MSYS2 MINGW64 shell, not $(MSYSTEM): start "MSYS2 MINGW64" from the Start menu)
endif
endif
WIN_CC ?= gcc
ZLIB_PREFIX ?= /mingw64
WIN_DIR = build/win64
HEADERS = $(wildcard host/*.h) Makefile
WIN_PLAT = host/plat/win_compat.c host/plat/win_sdcopy.c
WIN_LIB_SRC = $(filter-out host/azhost_main.c host/sdcopy.c,$(wildcard host/*.c)) $(WIN_PLAT)
WIN_CFLAGS = -std=gnu11 -D__USE_MINGW_ANSI_STDIO=1 -D_FILE_OFFSET_BITS=64 -O2 -g -Wall -Wextra -Werror -Wshadow -Wstrict-prototypes -Wmissing-prototypes \
             -isystem vendor -isystem vendor/include -isystem $(ZLIB_PREFIX)/include -Ihost -Ihost/plat
WIN_LDFLAGS = -static -static-libgcc -L$(ZLIB_PREFIX)/lib
WIN_HEADERS = $(HEADERS) $(wildcard host/plat/*.h)

all: build/libazhost.dll build/azhost.exe

win64: all build/test-host.exe build/test-version.exe

# the DLL exports what host/libazhost.exports lists (the leading underscore of the Mach-O list dropped into a .def)
$(WIN_DIR)/libazhost.def: host/libazhost.exports
	@mkdir -p $(WIN_DIR)
	(echo EXPORTS; sed 's/^_//' host/libazhost.exports) > $@

build/libazhost.dll: $(WIN_LIB_SRC) $(WIN_HEADERS) $(WIN_DIR)/libazhost.def
	$(WIN_CC) $(WIN_CFLAGS) -shared -o $@ $(WIN_LIB_SRC) $(WIN_DIR)/libazhost.def -Wl,--out-implib,$(WIN_DIR)/libazhost.a \
	    $(WIN_LDFLAGS) -lz -lpsapi -lbcrypt -lm

# azhost.exe links the DLL, and links win_sdcopy.o, profile.o, input.o and msg.o directly, as azhost does on the Mac
build/azhost.exe: host/azhost_main.c host/profile.c host/input.c host/msg.c $(WIN_PLAT) build/libazhost.dll $(WIN_HEADERS)
	$(WIN_CC) $(WIN_CFLAGS) -o $@ host/azhost_main.c host/profile.c host/input.c host/msg.c $(WIN_PLAT) \
	    $(WIN_LDFLAGS) -L$(WIN_DIR) -lazhost -lpsapi -lbcrypt -lm

build/test-version.exe: tests/test_version.c host/version.c $(WIN_HEADERS)
	@mkdir -p build
	$(WIN_CC) $(WIN_CFLAGS) -o $@ tests/test_version.c host/version.c $(WIN_LDFLAGS)

WIN_TEST_SRC = host/input.c host/match.c host/msg.c host/rawcopy.c host/crop.c host/png.c host/statemeta.c host/watch.c \
               host/profile.c $(WIN_PLAT) $(wildcard tests/host/*.c)

build/test-host.exe: $(WIN_TEST_SRC) $(WIN_HEADERS) $(wildcard tests/host/*.h)
	@mkdir -p build
	$(WIN_CC) $(WIN_CFLAGS) -ffp-contract=off -Itests/host -o $@ $(WIN_TEST_SRC) $(WIN_LDFLAGS) -lz -lpsapi -lbcrypt -lm

test-version: build/test-version.exe
	build/test-version.exe

test-host: build/test-host.exe
	build/test-host.exe

# static analysis of the Windows sources: one clang pass per file, no .plist output. analyze_assert.h makes the CRT's
# _assert noreturn for the analyzer, as on macOS.
check:
	tools/check-obinary.sh
	@command -v clang >/dev/null || { echo "check: clang not found (pacman -S mingw-w64-x86_64-clang)"; exit 1; }
	@rc=0; for f in host/azhost_main.c $(WIN_LIB_SRC); do \
	    echo "analyze $$f"; \
	    clang --analyze -Xclang -analyzer-werror -Xanalyzer -analyzer-output=text $(WIN_CFLAGS) \
	        -include host/plat/analyze_assert.h -o /dev/null $$f || { echo "check: FAIL $$f"; rc=1; }; \
	done; exit $$rc

testapp:
	$(MAKE) -C testapp

testapp-tone:
	$(MAKE) -C testapp-tone

clean:
	rm -rf build/libazhost.dll build/azhost.exe build/test-version.exe build/test-host.exe $(WIN_DIR)

.PHONY: all win64 check test-version test-host testapp testapp-tone clean

endif
