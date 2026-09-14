# Isolated authoring and multi-image calibration

The ordinary runner remains Python-standard-library-only. The Pixi
manifest/lockfile here supplies optional authoring tools and a consistent
GNU/MPI toolchain. Create its environment outside the repository and any
shared SDK. The lockfile resolves Linux x86-64 and macOS ARM packages;
the execution below was validated on macOS ARM.

The tested runtime is OpenCoarrays release `2.10.3`, commit
`3d0fa68dc95f05f9c17bd3e7dd0d34e6f530e429`, with GNU Fortran 14.4.0 and
MPICH 4.3.2. Do not silently replace this compiler with the separately
installed GNU 16 compiler: the runtime/compiler ABI is part of the
calibration.

Starting from the repository root, choose a new private workspace:

```sh
CAL=/path/to/new/private-calibration
mkdir -p "$CAL/env"
cp tools/calibration/pixi.toml tools/calibration/pixi.lock "$CAL/env/"
pixi install --locked --manifest-path "$CAL/env/pixi.toml"
git clone --depth 1 --branch 2.10.3 \
    https://github.com/sourceryinstitute/OpenCoarrays.git "$CAL/source"
git -C "$CAL/source" rev-parse HEAD
pixi run --manifest-path "$CAL/env/pixi.toml" cmake \
    -S "$CAL/source" -B "$CAL/build" -G Ninja \
    -DCMAKE_Fortran_COMPILER=mpifort -DCMAKE_C_COMPILER=mpicc \
    -DCMAKE_INSTALL_PREFIX="$CAL/install" \
    -DCAF_ENABLE_FAILED_IMAGES=OFF -DBUILD_SHARED_LIBS=OFF
pixi run --manifest-path "$CAL/env/pixi.toml" cmake \
    --build "$CAL/build" --target install -j 2
```

Check that the source commit equals the pinned value above before building.
The wrappers may print the short commit `3d0fa68` as their version; that is
the same pinned source, not a different release.

Run the actual existing cross-image case, forbidding a skip:

```sh
CAF="$CAL/install/bin/caf"
CAFRUN="$CAL/install/bin/cafrun"
pixi run --manifest-path "$CAL/env/pixi.toml" python tests/run_tests.py \
    --reference-only --no-skips --reference "$CAF" \
    --launcher "$CAF='$CAFRUN' -n {images} {exe}" \
    -t S10_2_1_3_023_valid__cross_image \
    --report "$CAL/two-image.json"
```

The runner recognizes the OpenCoarrays wrapper, queries its underlying
compiler, leaves its `-fcoarray=lib`/runtime link flags intact, and launches
two images. The source rejects fewer than two images and checks a remote
ordinary payload, so a successful result is not merely a single-image
compile. It does not inspect the undefined opaque components.

For a new, unapproved fixture, add `--allow-unreviewed` only while collecting
observations. This does not approve the fixture or permit an xfail update.

The same environment can regenerate the source census:

```sh
pixi run --manifest-path "$CAL/env/pixi.toml" python tools/import_standard.py \
    /path/to/24-007.pdf
python3 tests/suite_data.py --render
python3 tests/run_tests.py --audit
```

The importer rejects a PDF with the wrong checksum and stores section/unit
identifiers, locations, and content hashes rather than the standard's body
text. Its extraction still needs independent visual review and fine-grained
list/table subdivision. An internally consistent audit is not full source
closure; `--require-complete-source` remains false until that work is done.

## Freezing a target used during a long rollout

Do not rely solely on a version banner when another process is rebuilding
the target compiler. Select a private, immutable compiler snapshot with
`--lfortran /path/to/snapshot/bin/lfortran`. Preserve the matching runtime
libraries, intrinsic module files and advertised C binding header as well
as the executable. Record hashes of all copied inputs and verify the live
inputs stayed unchanged during copying.

Verify the relocated compiler's version and `--print-c-include-dir`, compile
and run a small intrinsic-module control, and check that the resulting
executable resolves the snapshot's runtime rather than the live build.
The September 14, 2026 development-build snapshot used an installed-layout
`share/lfortran/lib` path and a separate advertised `include/lfortran`
header location; do not guess those paths for another build.

Freezing and successful linking establish reproducible input bits, not a
compatible descriptor ABI. In particular, retain an observed
descriptor/header `CFI_VERSION` disagreement as a failed interface check.
Never substitute another compiler's header or change the expected version
to make it pass. Session-local snapshot manifests are uncommitted
observation artifacts; the rollout log records the selected version and
binary hash separately from source/fixture validity.
