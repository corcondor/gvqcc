# Full 75-word global ANGLE J-frontier — exact real KMBs, NOT official KickMix (2026-11-23)

CI SUCCESS: https://github.com/corcondor/gvqcc/actions/runs/45058408158

This is a measurement on the pinned **original public V8 ANGLE table** (1219 address rows ×75 rotations) and the SAME `signed6resid` multioutput tensor compiler at each J. Every KMB generated and independently checked for exact XOR on all legal addresses, arbitrary initial output words, all HMR phase coefficients and clean scratch registers.

| J | full KMB count | full 75-rotation CCX | max local Q | CCX delta vs J5 | GitHub status |
|---|---:|---:|---:|---:|---|
| 5 | 15 | 4154 | 126 | 0 | PASS |
| 6 | 13 | 4316 | 133 | +162 | PASS |
| 7 | 11 | **4067** | **140** | **-87** | PASS |

**Interpretation**
- J7 lowers actual full 75-rotation CCX by 87 (-2.094%) vs the **same compiler** J5, at an increased local width of +14Q.
- The first-three-bank screening had J6 T/word=54.83 vs J5=56, but its FULL cost is worse. This strictly demonstrates why partial-bank normalized costs are insufficient.
- The older PUBLIC **3357 CCX / 128Q family uses a more efficient synthesis method**. Therefore even full J7 still requires 710 fewer CCX to match that public T baseline. No score breakthrough has been demonstrated.
- Local Q values are **loader-specific**, not verified chemistry task total Q. Increased width can outweigh T savings in the official cost. Number of KMB files changes with J and must also satisfy the competition's loader contract and final reverse-pass semantics.
- Exactly the same FeMoCo angle table was used for all J; the underlying mathematical U and physical parameters were NOT changed by this grouping alone. However the full 18-file coupled scorer was **not** run.

**Reproduction**
GitHub workflow `.github/workflows/gvqcc-j-reblocking.yml` reconstructs the cryptographically pinned original V8 ANGLE/tree fixture, then invokes `research/claude_handoff_20261123/src/j_width_real_sweep.py` with `J=5,6,7`, full bank counts 15,13,11, including exact phase/value/scratch verifier. Artifacts are:
- `gvqcc-full75-J5-actual-KMB`
- `gvqcc-full75-J6-actual-KMB`
- `gvqcc-full75-J7-actual-KMB`

**Follow-up structure (no unverified promises)**
Retarget the PUBLIC 3357T sharing/caching compiler to J7 and measure full 75 words; current standalone J7 gains do not transfer automatically. Jointly co-optimize `J`, total Q, feeder register reuse, angle sign-field and physical W/H2/C/R, and run the true official KickMix simulator + complete score. Preserve negative J6 result as a regression.

**Verification boundary:** mathematical/local exact-phase PASS; official KickMix native not executed, no signed submission 18-file score, no new record.
