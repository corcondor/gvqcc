# Portable score5 DQI patch worker

`score5_patch_worker.py` is a self-contained Python standard-library worker. It
reconstructs the qualified DQI candidate from known inputs, packages it with an
incoming portfolio, and verifies every output member. It does not submit to
Kaggle, use the network, run a simulator, or repeat scientific verification.

## Exact target and accepted inputs

The default and currently sole target is `score5_6a`:

`6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02`

The embedded manifest accepts these external DQI hashes only:

| Input | SHA-256 | Applied stages |
|---|---|---|
| Exact4096 predecessor | `9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1` | Norm repair, 16 fan-out reductions, 8 fan-in reductions |
| Qualified norm repair | `ebfb770f6fc8abc7f48287a0fa4ee6404a2e32a9facdd38449b4f7b73be05d0e` | 16 fan-out reductions, 8 fan-in reductions |
| Final candidate | `6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02` | None; final SHA and portfolio still checked |

The internally verified intermediate after fan-out is
`98ad7b39a630a4152c54b39fbb14dece22fcaf34b00410ab8a45629db87e0b6f`.
An unknown DQI hash is rejected. `--target` chooses only names already embedded
in the pinned manifest; it is not an arbitrary patch or target-hash override.
Adding a future qualified target requires rebuilding the worker and publishing
its new manifest and worker hashes.

## Run

Only the generated `score5_patch_worker.py` is needed on the destination machine.

```sh
python score5_patch_worker.py \
  --source /path/to/input_portfolio.zip \
  --output /path/to/new_output/submission.zip
```

To reconstruct a standalone KMB from a known local KMB:

```sh
python score5_patch_worker.py \
  --dqi-only \
  --source /path/to/known_dqi.kmb \
  --output /path/to/new_output/dqi.kmb
```

`--dqi-only` also accepts a portfolio ZIP as its input. Output and receipt paths
must be new and separate from the input. There is no in-place replacement. The
default output directory, when `--output` is omitted, is `/kaggle/working`.
Arguments are explicit; the worker does not choose among unknown datasets.

The portfolio must contain exactly these 18 files: `invsqrt.kmb`, `dqi.kmb`,
`dfthcsos/submission.npz`, and `dfthcsos/angle_k_0.kmb` through
`dfthcsos/angle_k_14.kmb`. It may use a different incoming chemistry/invsqrt
portfolio. Every non-DQI payload is hashed on input, copied unchanged, hashed
again during packaging, and verified after reading the completed ZIP. This is
a byte-preservation guarantee; the worker does not infer that those incoming
17 files share the DQI target's scientific qualification.

## What is checked

Each exact byte patch checks the complete source size and SHA-256, every replaced
old region's SHA-256, every replacement's length and SHA-256, and the complete
result size and SHA-256. The final target is rehashed. The source input is
rehashed at the end to confirm that it was not changed.

ZIP output uses a fixed member order, timestamp 1980-01-01, Unix regular0644
permissions, and DEFLATE level6. All 18 output payload lengths, SHA-256 hashes,
and CRCs are read back. Deterministic ZIP bytes additionally depend on the
recorded Python/zlib implementation. ZIP metadata/compression is regenerated;
the guarantee for the other17 members concerns their exact uncompressed bytes.

The receipt stores the applied patch path, incoming and outgoing member hashes,
embedded manifest hash, source provenance, and the already-completed local
official DQI receipt. Companion evidence and license files remain outside the
18-member submission ZIP.

## Actual local exercise

The worker was executed once on
`/workspace/scratch/3815fb5fae06/score3_submission/submission.zip` and produced:

- Output: `/workspace/scratch/3815fb5fae06/score5_submission/submission.zip`
- Size: **63,553,158 bytes**.
- ZIP SHA-256: `bf426f2abce200a52a5243401078471fc940e9c393046860a988970530ada621`.
- Result: `PACKAGE_INTEGRITY_PASS`; all18 SHA/CRC checks passed; all17 non-DQI
  members preserved; runtime approximately24.95seconds.
- Worker SHA-256: `93222577d134739a3a0b1e005ac518b458548b33b023b92e92d3cfe7c6b290ea`.
- Receipt: `score5_patch_worker_check.json`.

This particular exercise deliberately preserved the requested score3 input's
score2 chemistry NPZ (`5f8dd37a…`). It did **not** substitute the later chemistry
candidate. The original score3 ZIP and all source/intermediate KMBs remain
unchanged.

## Existing local official result and scope

The embedded `score5_dqi_full_verification.json` is bound to the target6a SHA:

| Metric | Local official result |
|---|---:|
| Verification shots | 102400 |
| Value errors | 0 |
| Phase errors | 0 |
| Qubits | 889 |
| Static maximum Toffoli-like gates | 382896 |
| Mean Toffoli-like gates | 382068.47728515626 |
| DQI cost | 359709127680.1104 |

The verifier used its defaults (`seed=None`, empty salt, `log2_delta=-128`),
and its source SHA is checked. This is a local task cost, **not a Kaggle Public
Score**. Packaging does not create a new official verification or submission.

The norm repair extends the third public pivot to queriedD=0, queriedN≠0. The
known later node13 N=0 failure remains outside that repair. The 16+8 fan-out and
fan-in reductions preserve the predecessor's complete instrument, including
measurement phase feedback. A finite official PASS does not establish the
decoder on every possible input.

## Build and provenance

`score5_patch_build.py` exports the two operation recipes as exact byte patches
and verifies their complete virtual outputs before embedding them. It reuses
the frozen `outcome_dqi_chart_norm_patch.json.gz` for the first stage. The
portable patch-application method derives from
`outcome_dqi_chart_norm_worker_template.py`. The compiler helper imports
`kmb_profile.py` and `dqi_ccx_peephole.py`; the generated worker imports neither.

Run `python score5_patch_build.py` in the research checkout with the three pinned
KMBs available. Optional `--norm`, `--fanout`, and `--final` paths select their
locations, with all circuit hashes still pinned. The corresponding audited
`patch.json` and profile files are read from those candidates' directories.

Files for reproduction:

- `score5_patch_build.py` and `score5_patch_worker_template.py`.
- `score5_patch_worker.py`, `score5_patch_manifest.json`, and
  `score5_patch_worker_build.json`.
- `score5_patch_fanout16_recipe.json` and `score5_patch_fanin8_recipe.json`.
- `score5_patch_worker_check.json` and this README.
- Existing frozen norm patch, its proof/qualification, and
  `score5_dqi_full_verification.json`.

The upstream Apache-2.0 license and original DQI NOTICE, including existing
credits, are embedded and emitted next to the generated output.
