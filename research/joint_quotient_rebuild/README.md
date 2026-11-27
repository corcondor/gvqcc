# Joint quotient reconstruction (research, NOT SUBMISSION)

Use the user's exact 316k family, not the 419k decoder as a substitute. Keep all known defects as mandatory fail-closed tests. Use the V111 3262.5 expected paid/pass chemistry family with unchanged coefficient table.

## New mathematical result

Let C be the live Boolean-function space, U=C+E with the desired output directions E, pi:U→U/C, and u in C a candidate left factor. Set K0={a∈U: a|u=0=0}, K1={b∈U: b|u=1=0}. Then
{pi(uv): v∈C, uv∈U} = pi(K0)∩pi(K1).
Forward: a=uv, b=(1+u)v, with a+b=v∈C. Reverse: choose a,b with the same class; v=a+b∈C and uv=a. Thus solve two *linear* restriction problems rather than enumerating all right factors; get exact witnesses. This is a per-fixed-left-factor completeness result, not completeness of a finite left-factor dictionary. It supplies possible first innovations; independent control/target coordinates, schedules, phase, and full endpoint verification are still required before emitting gates.

For a measurement-free window with r independent nonlinear output directions and exactly r CCX, no intermediate nonlinear innovation may be outside the final nonlinear output span. In particular the first paid gate contributes a nonzero decomposable quadratic (polar rank 2) modulo affine functions. If the final nonlinear span contains no such direction, r gates are impossible on the full physical Boolean cube. This obstruction need not hold on the restricted reachable domain.

## Actual chemistry experiment

V111 bank6 SHA256 cf3fef592a0968cdec23073d03c84b1014e73a81f6927f97a592bafc2ffda991; NPZ SHA256 dcc713f35fcbe66ea80225b81363a8801893a9dbbf1ebf52f89b1b6ebfd06988. Native zero-based inclusive window [8991,9150]: 3 CCX; formal nonlinear dimension 2, all three nonzero directions have polar rank 4. No 2-CCX realization of the same transformation on the entire Boolean cube with affine gates and CCX (no measurements). On both legal directions of all 1219 addresses, dim C=129, dim U/C=2. Exact restriction search over 10,302 distinct left factors (address linear combinations, live physical wire functions, pairwise XOR modulo complements) against *all* right factors in C yielded no nonzero quotient class. It does not exhaust all u in C. Independent brute-force check of the restriction algorithm: 256 small spaces, 4494 exhaustive fixed-u tests, 1402 nonzero class witnesses, zero mismatches. No new chemistry circuit or paid saving yet.

Reproduction: extract GVQCC_V111_3262p5_300591_Chemistry_Both_Salts_PASS.zip and the chemistry/vendor directory from GVQCC_V112_Carry_Order_Code_Proofs_and_Research.zip (or the corresponding V110 research replay, matching its parser). Run:
```
python quotient_product.py /path/to/dfthcsos --vendor /path/to/vendor --out quotient_product.json --pairs
python test_quotient.py
```
Both input hashes must match. All experiment files in the separately delivered research bundle.

## Exact 316k diagnostic record (not a new repair)

The measured 62,086,097-op 900Q donor has SHA256 2c8ea3ad0cbf316b6392fb7ffd2fb04d3059633d8d66281228abe13b496c4e60, 311868 CCX, 6716 CCZ. This is **not** the 69,782,188-op 4b572141... donor of PR #225/#228. Zero-mask fixed weights [0,1,17,18,35] had baseline restoration bit errors [0,395,430,0,0]; 80,622 HMR events, single-event-flip phase errors [308,695,112,0,0], 320 separately bit-sliced histories agreed with the prior single-event evaluator. Native four-seed replay of these five inputs independently reproduced the value errors and variable phase failures. One-hot histories alone are NOT a universal certificate when adaptive measurement outcomes affect subsequent values. Boolean product differences require the mixed term. A phase-only patch cannot fix an incorrect computational-basis output. The exact scope/epoch pair scan examined all 311868 CCX and 6716 CCZ, found zero safe common-factor pairs by this conservative rule. An earlier 48 static CCX candidate had no executed paid improvement on this diagnostic panel and retained defects; not accepted.

Do not conflate the two 316k donor hashes or their validation panels. #228's 898Q prefix is useful width research but the full 900Q splice still has known failures, and is not a repaired decoder. No complete width/paid improvement, official verification, score, or submission is claimed by this PR. A future emitted candidate must pass exact local semantics plus independent whole-circuit checks; input-independent branch semantics and higher-order measurement phase must be closed.
