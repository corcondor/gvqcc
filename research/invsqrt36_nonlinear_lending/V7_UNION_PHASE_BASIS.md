# V7: union of guarded atlases, centralized phase basis, terminal-carry transport

2026-11-24. Diagnostic research, NOT a submission. Stacked on PR #36, do not merge into main. Shared source SHA256 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03, 60766 native instructions. Original expected 1406.3125 paid at 37Q. Goal is a real fully verified lower-cost oracle, not static count alone.

## Reconciled results
- #31 V5 53195 covered. #35 and #36 additions of 1101 and 554 source ops are disjoint; verified union 54850 covered (90.2643%), static 1925, expected 1733.3125; 42169 BDD compositions.
- On the union, #32 lifetime (-2), #37 joint delta (-11), #38 endpoint (-2) are exact-gate-matched and disjoint, inside certified 36Q charts. New phase-basis synthesis (-21), five actual edits: 8→1, 2→0, 8→3, 7→1, 4→3, on 47 paid runs / 53 paid blocks / 64 factor calls. Final 1889 static, 1710.8125 expected, 62394 checks, 1168 HMR variables; SHA e9b6536b0131127cca81ab21d4896d62037b98372427788bc2e8d5eb4a1eb156.
- #34 arithmetic inspiration: replace source [8096,8159) by a complete 7-stage operand-carry chain, preserving terminal event 8156. 128 holder choices, 7 removed HMRs (globally phase/rotation independent), carrier fitted in incoming coordinates q35 = q10 xor q14 xor q9*q10 xor q9*q14 xor q9*q27 xor q10*q14 xor q10*q27; factor needs 1 AND. Exact local PASS; full composition PASS 42110, +30 covered, +6 paid. Entry and exit HMR phase cancellation is necessary, not postselection. Earlier endpoint fit failed; don't repeat it.
- Recursive nested IF atlas: six ranges screened; four candidates, three accepted [32746,32818), [34046,34186), [35115,35207), +304 ops and +5 static; rejected [12356,12689). Combined with carry: 55184 covered (90.813942%), 5582 remain; 1936 static/1741.8125 expected; 41807 composition checks PASS, full serialized SHA 23bc16e069abe2462b30ae2fc8b4b01d4f69bd8cff1f41d54fd924771e596a7b. All 3133452 legal inputs and symbolic HMR histories.
- #33 and #39: do not add independent savings without exact splice. #39 epoch monomial/phase rank audit is useful for new cuts, but not equivalent to emitted native cost reduction.

## Core method
For contiguous diagonal guard bodies, derive Boolean ANF, factor cubic slices by GF(2) alternating form elimination, then select a weighted independent basis of the actual phase polynomials. Classical controls are XORs of original guards. Verify coefficients for every guard without assuming independence. CNOT conjugation is uncomputed. The concrete native edits are in the supplied archive's JSON receipts; Lean uses actual gate-list-derived SSA for three of the edits and the guard-basis formula for a fourth. It is not a Lean proof of the entire HMR instrument.

## Reproduce from the V7 research archive
cd central/global_chart
python v7_merge.py
python verify_portfolio.py v7union
python v7_integrate.py v7union
python v7_terminal_carry.py
python verify_portfolio.py v7carry
python v7_nested_atlas.py
python verify_portfolio.py v7nested
python v7_integrate.py v7nested
All native circuits here are *_NOT_SUBMIT.kmb. Do not submit the 37Q hybrids as a 36Q oracle. CI certifies only local identities. No new official score; main and official submissions unchanged.

## Additional reading (deduplicate against #34 and #39 bibliographies)
- Khoruzhii, Gelß, Pokutta, Tensor Decomposition for Non-Clifford Gate Minimization (2026), https://arxiv.org/abs/2602.15285; code https://github.com/ZIB-IOL/polytof (CCZ-specific tensor objective, unlike just T-count).
- Amy, Mosca, T-count optimization and Reed-Muller codes, https://arxiv.org/abs/1601.07363 (alternative equivalent phase representations; not a direct CCZ guarantee).
- Amy, Azimzadeh, Mosca, On the CNOT-complexity of CNOT-PHASE circuits, https://arxiv.org/abs/1712.01859 (parity networks and reversible restoration).
- Xu et al., Quartz, https://arxiv.org/abs/2204.09033 (verified rewrite generation, escape local minima).
- Nam et al., Automated optimization of large quantum circuits with continuous parameters, https://doi.org/10.1038/s41534-018-0072-4 (phase-aware long-range transformations).
- Wagner et al., QALM (2026), https://arxiv.org/abs/2606.16221 (alternate exploration and exploitation).
- Amy et al., meet-in-the-middle optimal synthesis, https://arxiv.org/abs/1206.0758 (exact small-window comparison).
These are reading/research directions. V7 actually implements cubic pair and quadratic-slice factorization, guard basis pooling, interval scheduling, terminal measurement transport, recursive guarded atlas and BDD checks. It does not claim to run the external optimizers.
