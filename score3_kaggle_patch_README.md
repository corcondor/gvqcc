# Finish the exact score3 portfolio on Kaggle

`score3_submit_worker.py` already rebuilds the exact4096 DQI circuit and
copies score2 chemistry into a complete `submission.zip`. It preserves the
older inverse `e46d90...`; this is the only remaining member to replace.

## Shortest route

The completed predecessor is notebook
[`geocpuresearch/gvqcc-exact4096-gauge-score2`, version 1](https://www.kaggle.com/code/geocpuresearch/gvqcc-exact4096-gauge-score2?scriptVersionId=369719696).
Use **`score3_kaggle_download_patch_cell.py`** (45,997 bytes) as one cell.
It calls the official SDK with
`kagglehub.notebook_output_download("geocpuresearch/gvqcc-exact4096-gauge-score2/versions/1", path="submission.zip")`,
checks the returned ZIP against SHA256
`1807d6ae6d2ea12b1d4bf2435f50d2513b25ade00fa0efb61390fdafb103ed37`,
copies it into `/kaggle/working`, and applies the embedded offline patch below.
It uses the SDK's returned path rather than guessing an input mount path.

**First run this cell interactively in the editor with Run All.** The SDK
attaches the source notebook output during that interactive run. Once the
attachment and cell execution have completed, use **Save & Run All** to create
the output version for submission. An initial Save & Run All without that
attachment was observed to stop at the SDK call with
`BackendError: New Notebooks cannot be attached in non-interactive sessions`
and `Version [1] requested, found no versions attached`. This is a session
capability restriction; the source cell and its checksum remain unchanged.
Do not treat that failed saved run as a successful package or submission.

The subsequent interactive Run All completed in 31.842 seconds in
`geocpuresearch/gvqcc-score3-exact4096-invsqrt-cache`. Its receipt reported
`exact_zip_bytes_reproduced=true`, 63,552,631 bytes, all eighteen member
SHA256/CRC checks passing, and final ZIP SHA256
`5a3011d3f208a0bae3b1e1bfb9b763ac8c7201f4de35a74d772699949b971882`.
Save & Run All version 2 then completed successfully in 45.9 seconds with
the input already attached. The full ZIP was submitted through the signed-in
Kaggle notebook-output submission UI. A new **Pending** row was observed at
2026-11-15 01:53:10 UTC for
[notebook version 2 / scriptVersionId 369722797](https://www.kaggle.com/code/geocpuresearch/gvqcc-score3-exact4096-invsqrt-cache?scriptVersionId=369722797).
The submitted ZIP has the exact final hash above and all eighteen member
SHA256/CRC checks passed. The submission ID was not exposed by the UI.
Public Score is not yet available; no Public Score improvement is claimed.
The observed submission record is
[`results/2026-11-15/kaggle_score3_cache_submission_369722797.json`](results/2026-11-15/kaggle_score3_cache_submission_369722797.json).

The notebook version number is `1`; its scriptVersionId is `369719696`.
The SDK handle uses `/versions/1`, not the scriptVersionId. The behavior and
API are described in the official
[kagglehub README](https://github.com/Kaggle/kagglehub/blob/main/README.md) and
[Kaggle cache resolver](https://github.com/Kaggle/kagglehub/blob/main/src/kagglehub/kaggle_cache_resolver.py).

## Offline or full rebuild alternatives

The self-contained **offline** choices are ready:

- `score3_kaggle_patch_offline.py` (44,388 bytes): append as a cell after an
  existing exact4096 output, without Internet access.
- `score3_kaggle_combined_cell.py` (273,752 bytes): the unchanged existing
  exact4096 worker followed by that offline inverse patch, suitable for one
  cell in a fresh notebook with the three required inputs below.

The offline patch was run once locally on a separate exact4096/score2
predecessor with the old inverse. It reproduced final ZIP SHA256
`5a3011d3f208a0bae3b1e1bfb9b763ac8c7201f4de35a74d772699949b971882`
exactly, with all eighteen member SHA256/CRC checks passing. The original
submission and circuits were untouched. Evidence is in
`score3_kaggle_offline_patch_check.json` and `score3_kaggle_offline_build.json`.

1. Run the existing `score3_submit_worker.py` cell. Its required inputs are
   the official competition data, `geocpuresearch/gvqcc-verified-480ccx-gauge128`
   notebook version 1 (scriptVersionId `369627280`), and
   `geocpuresearch/gvqcc-821-score2-verified` notebook version 1
   (scriptVersionId `369715705`). If its exact4096 output ZIP already exists,
   reuse it.
2. Run `score3_kaggle_patch_offline.py` as the next cell. It embeds the verified
   198,626-byte inverse, checks its SHA256 and the other seventeen members,
   then atomically replaces `/kaggle/working/submission.zip` with the final
   package. The smaller online variant `score3_kaggle_patch.py` instead
   downloads that same inverse from GitHub commit
   `b46c2535f2743be0b5d558b02a76bd62ee919055`.
3. Save and run the notebook. Choose its completed `submission.zip` output in
   the competition submission dialog.

For an attached predecessor ZIP, the equivalent script invocation is:

```bash
python score3_kaggle_patch.py --source /kaggle/input/PREDECESSOR/submission.zip --output /kaggle/working/submission.zip
```

An offline inverse file can be supplied with `--inverse-kmb PATH`.

## Exact pins

- DQI: `9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1`
- New inverse: `684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`
- NPZ: `5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357`
- All fifteen ANGLE loader hashes are embedded in the patch script.
- Reference final ZIP: `5a3011d3f208a0bae3b1e1bfb9b763ac8c7201f4de35a74d772699949b971882`

The reference uses Python 3.12.14 and zlib 1.3.2. Other zlib versions may change
compressed container bytes; every uncompressed member must still be identical.
The script records both checks in `score3_kaggle_patch_receipt.json`.
It performs packaging and checksum checks only. It does not run new quantum
tests, select seeds, optimize circuits, or submit to Kaggle.

`submission_v5_kaggle_worker.py` and its bestbase variant alone are insufficient:
their DQI hashes are respectively `e986d4...` and `821bf8...`, so the patch
refuses them until the exact4096 DQI worker has run.
