# V13 audit: 36Q is a hard constraint, not coverage

Independent PR59 wide replay: 40,984 comparisons, 199 exact splices, 3,133,452 legal inputs, 1,186 independent HMR variables, PASS. Both tracks' exact expected cost partition and dependency-depth proxy measured separately. See JSON. Header arity-three field was CCX-only; repaired metadata only, no changed instruction, no official verifier. PR59 Lean workflow success confirmed.

## Algebraic design hypothesis (not tested, not claimed novel)
For a positive odd integer a, let P=a*y, R=C-a*y^2. Append digit d in {0,1}, set y'=2y+d, C'=4C. Then P'=2P+a*d, R'=4R-d*(4P+a). Greedy digit test 4R>=4P+a gives next binary digit of sqrt(C/a) when y is its floor and the scaled target doubles. Because a is odd, d=P' mod 2, P=(P'-a*d)/2, R=(R'+d*(4P+a))/4. Thus one does not need a separate digit history to reverse this abstract recurrence; extract digit on reversal, subject to phase/ABI constraints. This is an exact integer identity, not a 36Q circuit. Full-width P/R may exceed width, odd/even normalization and fixed precision plus coherent phase need actual synthesis, and historical overlap remains unaudited. No novel-world-first claim. Do not execute search until source gate passes.

References for architecture comparison:
- Halpenny, Sireesh, Wallden, Fast, in-place, and ancilla-free quantum algorithms for integer multiplication and inversion (19 Nov 2026), https://arxiv.org/abs/2611.26605 (modular odd multiplier, not reciprocal square root).
- Yang, Yuan, MBUndo, https://arxiv.org/abs/2611.02345 (automatic measurement-based uncomputation).
- Paradis et al., Reqomp, https://doi.org/10.22331/q-2024-02-19-1258 (space-constrained uncomputation).
- Parent, Roetteler, Svore, Reversible circuit compilation with space constraints, https://arxiv.org/abs/1510.00377 (in-place functions/pebbling).
- Khattar, Gidney, conditionally clean ancillae, https://doi.org/10.22331/q-2025-05-21-1752 (borrowed registers; may already be in bibliography).
No claims these algorithms were implemented here or all are new citations.

The four missing ANGLE archives remain unavailable after cross-session and Library queries. No new candidate search, official score, full36Q or main change. Reproduction Python script, raw JSON and header-only KMBs supplied in companion archive. Lean file covers arithmetic facts on receipt and digit inversion only, not whole circuit.
