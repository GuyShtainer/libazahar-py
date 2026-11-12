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

build/azhost: build/obj/azhost_main.o build/libazhost.dylib
	$(CC) -o $@ build/obj/azhost_main.o -Lbuild -lazhost -Wl,-rpath,@loader_path

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

clean:
	rm -rf build/libazhost.dylib build/azhost build/test-version build/obj

.PHONY: all check test-version testapp clean
