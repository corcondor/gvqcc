# invsqrt coherent-window experiments

Input is the verified Q46 circuit `invsqrt_new/rebuilt_source.kmb`, SHA-256
`684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a`.
Experiments operate on intervals between observation boundaries, with only
X, CX, SWAP, CCX and CSWAP inside an interval.

- `window_rank.py`: uses 3,424 legal inputs to measure the increase in Boolean-function span from adding the after-window state to the before-window state. There were 2,583 windows of length 2–12 paid gates. In 118 windows the measured increase was smaller than the paid gate count. This is a necessary condition for an improvement in the tested affine-plus-products model.
- `rankone.py`: for lower-rank two-gate windows, computes the intersection of the before and after affine value spans. Tests products of one basis value, a two-value parity, or an available wire with an arbitrary affine combination of intersection values. It requires the model to induce the full after-window state via reversible affine frames. No fits were found with this control family.
- `multi_drop.py`: tries dropping any one of the existing paid gates inside a flagged window and synthesizing an exact affine reconciliation at its end. It tested 975 drops on 7,895 legal inputs with no hits. The script contains a separate complete-domain replay for sample hits, but no hits reached that stage.

No alternate KMB, full official run, or cost improvement came from this sweep. This is a bounded sample search and does not prove a general lower bound.

## Reproduction

The scripts import the prior `quick_inv/measure_linear.py` and `quick_inv/drop_reconcile.py` in the workspace. From the workspace root with Python, NumPy and KickMix available,

```sh
python quick_inv_score/window_rank.py --source invsqrt_new/rebuilt_source.kmb --out quick_inv_score/window_rank.json
python quick_inv_score/rankone.py --source invsqrt_new/rebuilt_source.kmb --windows quick_inv_score/window_rank.json --out quick_inv_score/rankone.json
python quick_inv_score/multi_drop.py --source invsqrt_new/rebuilt_source.kmb --windows quick_inv_score/window_rank.json --out quick_inv_score/multi_drop.json
```
