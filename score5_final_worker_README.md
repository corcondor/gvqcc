# Final score5 portable DQI worker

The final target adds two exact measured-target Toffoli reductions to the
qualified6a predecessor. Its raw KMB SHA-256 is:

`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`

`score5_final_worker.py` is a self-contained offline Python3.11+ standard-library
worker. The generated file is sufficient at runtime: KickMix, NumPy, the
research checkout, network access, and credentials are not required. The
worker never submits and never runs a new scientific verifier.

## Known-input reconstruction

The embedded manifest accepts DQI inputs pinned to9a82, ebfb,6a, or e4. Unknown
DQI hashes are rejected. The complete forward chain is:

| Stage | Result SHA-256 | Static maximum T |
|---|---|---:|
| Exact4096 input | `9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1` | 382934 |
| Projective norm repair | `ebfb770f6fc8abc7f48287a0fa4ee6404a2e32a9facdd38449b4f7b73be05d0e` | 382920 |
| 16 fan-out reductions | `98ad7b39a630a4152c54b39fbb14dece22fcaf34b00410ab8a45629db87e0b6f` | 382904 |
| 8 fan-in reductions | `6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02` | 382896 |
| 2 measured-target reductions | `e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355` | 382894 |

The final circuit uses Q889 and208169 classical bits. The last stage removes
two unconditional CCX, adds two measurement-conditioned CZ, preserves the HMR
count, and adds two private classical measurement bits. It requires no extra
quantum wire.

Each patch verifies every changed old/new byte region and the entire input and
output SHA-256 and length. The worker follows only the embedded, pinned patch
chain. The default target is `score5_e4`; `--target score5_6a` can select the
preserved earlier target for a compatible earlier input. There is no reverse
patch from e4 to6a and no arbitrary target or patch-file override. Qualification
receipts are selected and SHA-checked separately for each target.

## Usage

```sh
python score5_final_worker.py \
  --source /path/to/known_portfolio.zip \
  --output /path/to/new_directory/submission.zip
```

For a standalone KMB:

```sh
python score5_final_worker.py \
  --dqi-only \
  --source /path/to/known_dqi.kmb \
  --output /path/to/new_directory/dqi.kmb
```

Output and receipt paths must be new, distinct files. Existing artifacts are
not replaced. `--dqi-only` also accepts a portfolio ZIP and emits only its
patched DQI. When omitted, `--output` defaults to `/kaggle/working` with the
appropriate filename. The notebook/script must provide an explicit input path.

A portfolio input must contain exactly `invsqrt.kmb`, `dqi.kmb`,
`dfthcsos/submission.npz`, and the15 `dfthcsos/angle_k_0.kmb` through
`dfthcsos/angle_k_14.kmb` files. All17 non-DQI payloads are preserved exactly.
They are hashed on input, during copying, and after the completed ZIP is read
back. All18 output lengths/SHA-256 hashes/CRCs are checked. ZIP metadata and
compression are regenerated deterministically for the recorded Python/zlib
version; the non-DQI guarantee concerns the uncompressed payload bytes.

The worker does not silently replace chemistry or inverse-square-root files.
Their incoming payloads may belong to a different qualified portfolio, so
preservation alone is not a claim of new scientific qualification for them.
License, notice, manifest, and verification companions remain outside the
exact18-member submission archive.

## Exact phase and classical timing evidence

The identity used by the last stage is

\[
M_m X_t^{ab}=(-1)^{mab}M_m,
\qquad M_m=|0\rangle\frac{\langle0|+(-1)^m\langle1|}{\sqrt2}.
\]

It holds separately for each measurement outcome on arbitrary superpositions
and entangled references. All intervening operations act trivially on the
measured target. The early HMR writes a new private bit; the corresponding
conditional CZ replaces the old CCX. Only at the original HMR position does
`BIT_STORE0; BIT_INVERT_IF` copy the new result into the original outcome bit.

This timing is material: the two original outcome bits are read51 and167 times,
and written2 and224 times, respectively, inside the intervals. Those existing
operations remain byte-identical. The independent audit checks64 Kraus
entries, both complete intervals, every unaffected instruction column, the
unchanged register bytes, and the exact allowed header changes. See
`score5_dqi_hmr_independent_review.json` and its independent implementation.

## Build and scope

`score5_final_worker_build.py` requires the pinned e4 candidate, its four-edit
recipe, its independent review, and a completed default102400-shot official
receipt with zero value/phase errors. It will not seal the worker with the6a
receipt substituted for e4. It uses a strict five-opcode encoder for this HMR
patch and validates the virtual reconstruction's full e4 hash.

The builder extends the frozen `score5_patch_worker.py` payload; it does not
modify that earlier worker or the existing6a ZIP. Research-side build helpers
are listed by their hashes, while the generated worker has only standard
library dependencies. Reproduce from the pinned checkout with:

```sh
python score5_final_worker_build.py
```

## Completed local official check

The final e4 receipt completed before the worker was sealed:

| Metric | Local official result |
|---|---:|
| Shots | 102400 |
| Value errors | 0 |
| Phase errors | 0 |
| Qubits | 889 |
| Classical bits | 208169 |
| Static maximum Toffoli-like gates | 382894 |
| Mean Toffoli-like gates | 382066.52936523437 |
| DQI task cost | 359707293756.04297 |

The receipt uses the verifier defaults (`seed=None`, empty salt,
`log2_delta=-128`) and is SHA-bound to the final e4 KMB. Its SHA-256 is
`3b59268e86faedf7026ef4b53b2428675dd7bb3f031cee61e5eb5dfb236df043`.
The standalone worker is159,959bytes with SHA-256
`f2e9187bfc754712e139098aed195895b189fd203e174015d898198bd8c0578e`.
The final embedded manifest SHA-256 is
`6cf356b86aba9b5f2d09a4e470fd72f52a0fe25193c753e395f1c5cc62b94172`.
The packager did not rerun this scientific verification.

## Completed reconstruction and ZIP readback

The sealed worker was executed once with the existing score3 portfolio as its
input. It reconstructed all four stages, starting from9a82, and verified each
complete intermediate circuit hash before proceeding.

- Output: `/workspace/scratch/3815fb5fae06/score5_final_submission/submission.zip`.
- ZIP size: **63,553,234 bytes**.
- ZIP SHA-256: `7b59403add6ec475513b9f1f634781cfc563cd5acdc50970db03c91ad3d03978`.
- Final DQI size:522,343,175bytes, with the e4 SHA shown above.
- Result:`PACKAGE_INTEGRITY_PASS`; all18 member SHA/CRC checks passed; all17
  non-DQI payloads preserved; runtime approximately30.85seconds.
- Reproduction receipt:`score5_final_worker_check.json`.

This requested exercise preserves score3's score2 chemistry NPZ (`5f8dd37a…`)
and inverse-square-root candidate (`684106f1…`). It does not replace them with a
later portfolio. The input score3 ZIP and the previous6a worker/ZIP remain
unchanged. A different known-DQI portfolio can be supplied to preserve its own
17 other members using the same worker.

The norm repair covers queriedD=0, queriedN≠0 at the third public pivot. The
known later node13 numerator-zero failure remains outside that class. A finite
official PASS is not a proof of universal decoder correctness. All reported
costs are local official task costs; this work does not claim a new observed
Kaggle Public Score or submission.
