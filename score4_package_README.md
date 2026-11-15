# Offline score4 DQI patch and submission ZIP

`score4_package_cell.py` is a self-contained Python cell. It uses only the
standard library and makes no network requests. Run it after the existing
score3 notebook cell has produced `/kaggle/working/submission.zip`.

The expected source archive is the complete score3 portfolio:

- ZIP SHA256:
  `5a3011d3f208a0bae3b1e1bfb9b763ac8c7201f4de35a74d772699949b971882`.
- Source DQI SHA256:
  `9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1`.
- Target DQI SHA256:
  `5a60d66233198be8ce05d9710bd35a7d2d6700bbced87560d405651070ae8194`.
- The inverse, chemistry NPZ, and fifteen ANGLE loaders retain their exact
  seventeen source-member SHA256 pins from `score3_submission_manifest.json`.

The cell embeds compressed, checksum-bound copies of `kmb_profile.py`,
`dqi_ccx_peephole.py`, the fixed 32-edit recipe, and all eighteen archive
member pins. The recipe replaces 32 old CCX instructions with 16 CCX and
32 CX instructions. The old operation bytes are checked before rewriting;
the rebuilt DQI must match the exact target SHA256 before packaging proceeds.

## Kaggle execution

1. Run the existing score3 cell and then paste/run `score4_package_cell.py`.
2. The second cell patches `/kaggle/working/submission.zip` atomically after
   checking the complete replacement archive. A failure leaves the source
   archive intact. Temporary uncompressed circuits are removed on exit.
3. Inspect `score4_package_receipt.json` and the final `submission.zip` output.
   Saving/running the notebook and competition submission are separate UI
   actions; this cell does not perform either action.

The receipt reports every member's SHA256 and CRC. The archive uses the same
deterministic metadata as score3: fixed member order, 1980-01-01 timestamps,
Unix regular-file permissions 0644, DEFLATE level 6, and no comments, extra
fields, directory entries, or ZIP64 records. Compression-library differences
can change container bytes while preserving every exact circuit member.

The cell supports rerunning in place when the input already contains the
exact target member set. It refuses an unrelated source or a separate
preexisting output path.

## Local reproduction

The same cell can be executed as a script:

```bash
python score4_package_cell.py \
  --source /path/to/score3/submission.zip \
  --output /path/to/score4/submission.zip \
  --receipt /path/to/score4_package_receipt.json
```

To regenerate the standalone cell from this repository, run:

```bash
python score4_package_build.py
```

The generator uses the committed `score4_package_template.py`,
`score4_package_recipe.json`, `score3_submission_manifest.json`, and the two
modules named above. It needs no scratch-only file. The standalone generated
cell itself needs none of those adjacent files.

## Validation boundary

This code validates packaging and exact byte identity. It does not rerun
KickMix or the competition verifier, choose verifier seeds, optimize a new
recipe, or claim a Public Score gain. The separate official DQI receipt must
bind the target `5a60d662…` circuit. The local packaging receipt preserves the
verification status observed at build time; the package manifest records any
later bound official result separately.
