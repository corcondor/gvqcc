# Independent review: norm-integrated projective chart

**PASS for the declared finite-output chart contract.** Reviewed complete
candidate SHA-256:
`ebfb770f6fc8abc7f48287a0fa4ee6404a2e32a9facdd38449b4f7b73be05d0e`.
The earlier `+118 T` review is retained separately. This review concerns
the newer `-14 static T` candidate and changes no candidate file.

## Why the one-Toffoli flag is exact

The modified inverse passes `zero_flag` to the existing
`cubic_inverse130.inverse_six_cubic` API. That implementation computes the
two-bit GF(4) norm, applies `X` to both bits, applies one ordinary `CCX` to
the flag, and restores both norm bits. Therefore it performs
`flag ^= [norm == 0]`; it does not require a zero flag or overwrite its
previous state. The outer wrapper requires a separate quantum flag, while
the caller keeps that wire allocated throughout the inverse.

Every nonzero element of a finite field has a nonzero field norm. The
actual quadratic constants are 2048 for GF(2^24)/GF(2^12) and 42 for
GF(2^12)/GF(2^6); their respective absolute traces are both one, confirming
the irreducible quadratic extensions used here. The last norm is
`x^(1+4+16) = x^21` from GF(2^6) to GF(4). Its supplied Boolean certificate
and its zero predicate were independently evaluated on all 64 inputs.
Consequently the three successive norms vanish exactly when the original
24-bit input vanishes.

## Coherence, inverse return, and resources

The added operation is a coherent XOR into a dirty flag. It does not
measure the flag or change the norm. The existing scaffold HMR cleanup
still repays exactly its original phase from the preserved source. This
remains valid when the flag is entangled with that source: the phase is the
same diagonal function and the cancellation holds on every basis state.

The three deferred six-bit inverse masks and their repayment code are
unchanged. In the return, the toggle has moved inside the inverse; this is
equivalent to its previous position because zero is invariant under
`inv0`. Thus each saved mask is still repaid against its correct inverse
witness. The projective chart's final flags remain zero on `N2 != 0`,
including `D2 = 0`, as proved in the earlier review.

The optional flag adds no helpers. The production maximum remains
`864 retained + 1 flag + 24 inverse helpers = 889 qubits`.
The new ledger is:

| Quantity | T count |
| --- | ---: |
| Prefix | `3*192 + 2*24 = 624` |
| Return | `3*196 + 2*24 = 636` |
| Pair | `1260` |
| Change from original public pair | `-14 static; -3 expected` |

The expected-count difference accounts for removal of the old flag's
average 11-T conditional cleanup discount. The complete candidate has
382,920 static Toffoli-like operations.

## Independent executable check and bound evidence

The review script ran the GF(2^6) inverse on its **entire 64-value source
domain**, both old flag values, and clean/dirty inverse targets: 256 cases
under each of three HMR seeds. Source, target XOR, dirty flag XOR,
bystanders, scratch cleanup, and phase all had **zero errors**. This is an
independent test of the newly used dirty-flag API rather than a rerun of
the collaborator's chart test.

The collaborator's chart report additionally records 3,074 finite-output
cases under four HMR seeds, with zero value and phase errors. The complete
verifier report is now **PASS on the default 102,400 shots**, with zero
value/phase errors, Q=889, mean T=382092.5565332031, and DQI cost
359731797766.2993. This reviewer read that report and independently hashed
the complete KMB to bind it to the reported circuit; the expensive full
verifier was not rerun.

The mathematical exactness claim remains scoped to finite raw `Y` with
`N2 != 0`. The known later zero-numerator failure is not solved, and a
finite verifier panel is not a proof of correctness on all decoder inputs.

Machine-readable hashes, constants, test records, resource counts, and
external-evidence attribution are in `outcome_dqi_chart_norm_review.json`.
The reproducible independent check is `outcome_dqi_chart_norm_review.py`.
