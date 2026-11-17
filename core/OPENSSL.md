# The OpenSSL our core links

The core `azahar_lazpy_libretro.dylib` links OpenSSL 3.6.5 statically (`libssl.a`, `libcrypto.a`), Apache-2.0. This
file says where those libraries came from and how to build the same ones. The release attaches the exact source
tarball.

- Version: 3.6.5.
- Source: `https://github.com/openssl/openssl/releases/download/openssl-3.6.5/openssl-3.6.5.tar.gz`, sha256
  `a2157c2830efdec3788939b00c9b0638306d3f0bbb76dc4832ee503bb397df98` (the value in the keg's SBOM and OpenSSL's
  published `.sha256` file; the release asset `openssl-3.6.5.tar.gz` is this exact file).
- The libraries are the Homebrew `openssl@3` bottle, sha256
  `0994a8029175af4578c3b93b3020e58dffa638ca21dc22d862c6bc02fea7e73b`, built 2026-09-29T17:47:00Z from the source
  above, no patches (the bottle's SBOM lists none). They were installed in the Cellar folder
  `/opt/homebrew/Cellar/openssl@3/3.6.5`; `tools/build-core.sh` resolves `/opt/homebrew/opt/openssl@3` to it.
- The two archives the link used (sha256, also in the release's `build.inputs`):
  `libssl.a` `23c6a50d6e01660db8ad58ed2f71305bf634970f044be2289b18d55ebc0370d9`,
  `libcrypto.a` `88981a4c6ce3c36127d12f6e7053b926d8a70ec1dbd0fa259113e6c8514a0583`.
- The formula the bottle was built from: homebrew-core `Formula/o/openssl@3.rb`, sha256
  `8fa691c3aade8a06699a7f36f11bf66dd81a7747f9163642a08d71df155a3853` (the copy the keg holds); the homebrew-core
  commit is not recorded in the keg. Its configure arguments, quoted:

```ruby
args = %W[
  --prefix=#{prefix}
  --openssldir=#{openssldir}
  --libdir=lib
  no-ssl3
  no-ssl3-method
  no-zlib
]
arch_args += %W[darwin64-#{Hardware::CPU.arch}-cc enable-ec_nistp_64_gcc_128]
system "perl", "./Configure", *(configure_args + arch_args)
```

- `openssl version -a` of that build:

```text
platform: darwin64-arm64-cc
compiler: clang -fPIC -arch arm64 -O3 -Wall -DL_ENDIAN -DOPENSSL_PIC -D_REENTRANT -DOPENSSL_BUILDING_OPENSSL -DNDEBUG
OPENSSLDIR: "/opt/homebrew/etc/openssl@3"
```

## Rebuilding

Homebrew ships only its current `openssl@3`. If that is 3.6.5, `tools/build-core.sh` finds it. If not, build 3.6.5
from the release's `openssl-3.6.5.tar.gz` yourself. This recipe is **not tested by this project**:

```sh
tar -xzf openssl-3.6.5.tar.gz && cd openssl-3.6.5
./Configure darwin64-arm64-cc --prefix=<dir> --openssldir=<dir>/ssl --libdir=lib no-shared no-ssl3 no-ssl3-method no-zlib enable-ec_nistp_64_gcc_128
make && make install_sw
```

Then `LAZ_OPENSSL_PREFIX=<dir>` and `LAZ_CORE_PIN=core/PIN-nokeys tools/build-core.sh --build`. A core built that way
links OpenSSL's code from the same source, but its `libssl.a` and `libcrypto.a` will not be byte-identical to the
ones above.

## Windows (x64) build

The Windows core `azahar_lazpy_libretro.dll` links its own static OpenSSL 3.6.5, built from the same source tarball
(`openssl-3.6.5.tar.gz`, sha256 `a2157c2830efdec3788939b00c9b0638306d3f0bbb76dc4832ee503bb397df98`, no patches).
`tools/build-core-win64.sh` builds it, in CI, inside the pinned container named in `build.inputs` (`image=`).

- Compiler: Ubuntu 26.04's mingw-w64 GCC with posix threads (`x86_64-w64-mingw32-gcc-posix`). The exact package
  versions are the `mingw_pkg` lines in the release's `build.inputs`.
- Configure line (also recorded as `openssl_configure` in `build.inputs`):

```sh
CC=gcc-posix ./Configure mingw64 no-shared no-tests no-ssl3 no-ssl3-method no-zlib --cross-compile-prefix=x86_64-w64-mingw32- --prefix=/opt/lazpy/openssl-3.6.5-mingw64 --openssldir="C:/Program Files/Common Files/SSL" --libdir=lib
make -j build_libs
make install_dev
```

- The source hash is recorded as `openssl_src_sha256` in `build.inputs`; the build refuses a tarball that does not
  match the value in this file.
- The two archives the link used (sha256, also in `build.inputs`): `libssl.a` `TO BE FILLED from the first CI run
  (openssl_libssl_sha256)`, `libcrypto.a` `TO BE FILLED from the first CI run (openssl_libcrypto_sha256)`.
- The `--openssldir` path is a Windows path that the core never reads: no OpenSSL config, engine or module is loaded.
  The build records the OPENSSLDIR, ENGINESDIR and MODULESDIR strings found in the DLL in `build.inputs`.
- Rebuilding: run the `core-win64` workflow, or follow the same steps in a mingw-w64 cross environment. Libraries
  built elsewhere link the same OpenSSL code but will not be byte-identical.
