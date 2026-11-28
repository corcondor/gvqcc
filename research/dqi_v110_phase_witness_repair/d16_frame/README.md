# D16 output-frame audit and verified historical splice

Research only. [PR #278](https://github.com/corcondor/gvqcc/pull/278) source-export artifact 15253007858 (ZIP SHA-256 `ac1706994a8e6c7c7ca06444280ae8643d4d48765ad340274b363852ff3deacc`) includes the source arithmetic.py and d16/ tables used here. [PR #294](https://github.com/corcondor/gvqcc/pull/294) supplies the polar lower bounds. W70 and W84 have attainable five- and six-product bounds in the isolated linear-parity product model, respectively. Their explicit affine-corrected witness identities and the shear lemma pass strict Lean 4.35.0. The witnesses are not used to replace the same-cost original products.

`audit_products.py` confirms eight physical blocks, fourteen isolated six-input groups in each, already at those per-group bounds (4 × 70 + 4 × 84 = 616 CCX). The proof is local, not global. Every pair of input spans has rank 12. Triples (5,6,7), (8,9,10), and (11,12,13), zero-based, also have rank 12 instead of 18. On each such triple the 15 or 18 original independent polars were the only decomposable polars in their span; any improvement there must leave that span. This does not rule out auxiliary product polars outside the original span, cross-frame sharing or HMR-aware simplification.

An output basis change makes all CNOT fanout act once per block instead of once per product. Select independent physical output rows of the coefficient map. For retained outputs (u), other outputs (v), linear extension (F), and retained delta (d), use ((u,v)\mapsto(u,v\oplus F(u))), apply the original products to (u), then undo the same shear. This adds (F(d)) to (v) even when pre-existing output bits are dirty. Width and nonlinear products are unchanged. This pure X/CX/CCX permutation has no phases or measurements.

The four W84 spans were uniquely matched by exact full gate sequences in historical public V7 (SHA-256 `4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52`). Actual spliced KMB SHA-256 `c35f2d216708fd42b02d7c40c8cd297e34cf10e42a3a6b0001c25e0c056380f5`: 900 Q, 69,782,188 → 69,733,422 instructions, all 48,766 cuts CNOT; CCX 312,254 and Toffoli-like 318,972 unchanged. W70 did not improve. The full #279 artifact (SHA-256 `518d634ede9dcf7e78a8e91264db25d544f54bf3c86caee7ebc355f618a66499`) did not match any of the four emitted spans or their entire paid subsequences. No splice on #279, no score gain or repair claim.

KickMix 1.0.0: 1,691 component inputs per old/new physical stage, including all 667 degree-two determining probes, random output contents and random inputs. In the paired whole-tape check, all restored syndrome bits, mask bits, workspace and raw phases matched on 256 common shots, with identical executed paid counts. The usual-distribution subset had 0/120 value errors; 136/136 lower-weight stress shots still failed on both, with 73 raw phase disagreements on each. No official verification/submission.

## Reproduce

In a new working directory, extract the #278 source export and place these scripts beside `arithmetic.py`. Set PYTHONPATH to KickMix 1.0.0 and the official DQI verifier directory. Obtain the pinned public V7 KMB and `native.hpp` from commit `c94c53a38674697e2f7ed57134b0a88ed2d75a23`, path `research/dqi316k_joint_crt/native.hpp`.

```sh
python audit_products.py d16
python triples.py     # only decomposables inside each exceptional 12-input triple span
python output_frame.py d16 coupons
python - <<'PY'
from pathlib import Path
import kickmix as km
for p in Path('coupons').glob('*84*.kmx'):
    km.Circuit.from_file(p,format='kmx').to_file(p.with_suffix('.kmb'),format='kmb')
PY
c++ -O3 -std=c++17 splice.cpp -o splice
./splice v7.dqi.kmb v7_d16_shear.kmb coupons/field_{1,2,3,4}_wiring_84.{old,new}.kmb
python paired_full.py v7.dqi.kmb v7_d16_shear.kmb
lean -DwarningAsError=true lean_identity.lean
```
