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

.PHONY: all check test-version test-host testapp clean win64

# Windows probe host (branch probe-win): "azhost.exe run" and "layout" only, one static exe, mingw-w64 (posix threads).
#   make win64 [ZLIB_PREFIX=<prefix of a mingw-built zlib>]
# State, SD seeding and the tree walk live in host/plat/win_stubs.c and return AZH_E_UNSUPPORTED.
WIN_CC ?= x86_64-w64-mingw32-gcc-posix
ZLIB_PREFIX ?= $(HOME)/3ds/zlib-mingw
WIN_SRC = $(filter-out host/azhost_main.c host/sdcopy.c host/state.c host/statemeta.c,$(wildcard host/*.c)) $(wildcard host/plat/*.c)
WIN_CFLAGS = -std=gnu11 -D__USE_MINGW_ANSI_STDIO=1 -O2 -g -Wall -Wextra -Werror -Wshadow -Wstrict-prototypes -Wmissing-prototypes \
             -isystem vendor -isystem vendor/include -isystem $(ZLIB_PREFIX)/include -Ihost -Ihost/plat

win64: build/win64/azhost.exe

build/win64/azhost.exe: $(WIN_SRC) host/azhost_main.c $(HEADERS) $(wildcard host/plat/*.h)
	@mkdir -p build/win64
	$(WIN_CC) $(WIN_CFLAGS) -o $@ host/azhost_main.c $(WIN_SRC) -static -static-libgcc -L$(ZLIB_PREFIX)/lib -lz -lpsapi -lm
