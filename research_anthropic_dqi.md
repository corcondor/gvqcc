# Anthropic DQI paper versus the actual 821 decoder

Audit date: 2026-11-14. This is a source and resource-model comparison. No candidate was rebuilt, no full simulation was run, and the verified `e986d416…` candidate and pinned pipelines were not changed.

## Conclusion

The paper provides a useful independent architecture and, especially, a method for recovering reversible history from the current state. Its reported **12× improvement is against the Khattar reference EEA decoder, not against our 821 public baseline**. The current decoder is already a much more specialized, in-place rational-interpolation design. It contains projective arithmetic, a rolling flag, measurement-based cleanup, and reconstruction of erased predicates. Calling its whole central region simply “the old EEA” obscures these differences.

The paper's gate counts and our Kickmix counts are **reference values from different evaluation systems; they cannot be compared directly until the proposed circuit is translated to the official ABI and evaluated there**. In particular, its classical-control charging, fixed mask, correctness allowance, and objective differ. The 1,837 versus 889 qubit counts also make the public BM implementation an unattractive immediate replacement, but this is not a proof that every BM redesign is inferior.

## Primary sources and acquisition

- [Paper, arXiv:2610.22367v1](https://arxiv.org/html/2610.22367v1), submitted 15 October 2026, especially Table 1 and SI I.1.
- [Anthropic article, 16 October 2026](https://www.anthropic.com/research/designing-efficient-quantum-circuits).
- [Pinned author repository](https://github.com/andigu/uncompute/tree/64b5a13aa249f1360846657392e6c66817b26d0f).
- [Published DQI results](https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/dqi-reed-solomon/results.jsonl).
- [Detailed discovered-circuit explanation](https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/tasks/dqi-reed-solomon/circuits/discovered/README.md).
- [Builder cost and measurement semantics](https://github.com/andigu/uncompute/blob/64b5a13aa249f1360846657392e6c66817b26d0f/uncompute/README.md).

The twelve downloaded DQI text files under `../official_sources/Anthropic_uncompute/tasks/dqi-reed-solomon/` were independently checked against Git blob hashes in commit `64b5a13aa249f1360846657392e6c66817b26d0f`. Receipts are in `../official_sources/Anthropic_uncompute/dqi_download_manifest.json`. The downloaded `circuit.py` SHA-256 is `d5f7dd55915e3426ab87ec75da5b76a37123cb996cd750f46ecd74be17a5ec30`.

## What the paper contributes

For the same 70 twelve-bit syndrome, 4,095-position, weight-at-most-35 Reed–Solomon problem, the paper uses 70 Berlekamp–Massey rounds instead of the reference's 222 synchronized EEA cycles. Conditional swaps route both update cases through shared arithmetic. Rescaling maintains `sigma[0] * delta = 1`; most discrepancies can therefore be reconstructed during reversal. Exceptional retained discrepancies use one 19-qubit tagged slot instead of a worst-case 665-qubit stack. Sampled coefficient cutoffs and stack overflow consume a bounded error budget. Its other ingredients include in-place evaluator construction and phase-only recovery using a precomputed reciprocal polynomial. These are descriptions of that architecture, not claims that the same savings remain available in 821.

## Resource values and why the scores differ

| Circuit | Reported Toffoli quantity | Q | Provenance |
|---|---:|---:|---|
| Author's Khattar EEA reconstruction | 5,125,070 | 1,938 | `results.jsonl`, emitted-stream count in the author's evaluator |
| Author's discovered BM circuit | 442,397 | 1,837 | Same file and evaluator; TQ = 812,683,289 |
| Actual 821 baseline, paired sample | 382,599.9932617188 | 889 | Official local verifier, 102,400 inputs matching v2 |
| Our separate 480+gauge128 candidate | 382,115.5671582031 | 889 | Official local verifier, default 102,400 inputs |

The last two rows are a valid paired comparison: both have zero value and phase errors on the same inputs, and the candidate saves 484.426103515625 executed Toffoli equivalents per shot. Its full local cost is 359,753,461,767.22644. See `dqi_combined_v2_report.md` and `dqi_combined_v2_paired_comparison.json`; a Kaggle public-score improvement is not established by these local runs.

Do not divide the first two rows by the last two to claim a competition gain:

- The paper ranks by `T * Q`. The official DQI verifier computes `R * Q**2 * mean_executed_Toffoli_like`, with `R` determined by the confidence bound on detected errors.
- The author's Builder charges classical `Bit`-controlled CX as CCX and classical `Bit`-controlled CZ as CCZ. Its documented T is constant for the emitted stream. The Kickmix verifier instead reads execution statistics over shots and separately reports the static maximum.
- The published DQI circuit uses a fixed random phase mask and hardcodes the resulting interpolation and skipped points. The official verifier supplies a fresh, arbitrary classical mask array per shot. A valid port must accept and restore those input registers; importing its fixed-mask circuit is insufficient.
- The paper accepts up to 100 wrong signs in 100,000 tests. The competition has its own error penalty and confidence calculation. Its empirical rare-event frequencies are useful design evidence, not a replacement for that verifier.

## Positive evidence for the current architecture

All source paths in this section are relative to `../official_sources/Syed_v12/source/dqi_source/src/controller_work/`.

The public manifest attributes actual `821bf8d157c0…` to Syed's v12 889-qubit decoder, rebuilt at extractor cutoff 18 with 241 retained products. The shipped unmodified Syed generator builds ancestor `7cbe8ecf6f6e…`, not 821. The distinctions below follow the positive import/call chain of that ancestor and verified shared arithmetic in the actual binary; they are not a claim that we reproduced the complete 821 derivative from unmodified source.

1. **Production chain.** `after_v3/integration_v7/v7_pipeline.py:configure` loads `after_v3/blocks/accepted_runtime.py`, which binds the accepted `after_c5/integration_v3/integrated_pipeline.py` with all four options. v7 then explicitly replaces the extractor, arithmetic, preimage, transpose and scan providers. `emit_key_prefix` is forwarded into that pipeline.
2. **Syndromes are reused in place.** `night_c27/synthesis/public_geometry.py:emit` changes the 840 input wires to residues at 35 public quadratic nodes. `integrated_pipeline.py:emit_key_prefix` pairs the 70 input words into 35 GF(2^24) words, allocates one 24-qubit carry, extracts quotient heads, then synthesizes numerator and locator in those same registers. This is not the author's separate `SIG` and `BB` BM banks.
3. **The actual extractor is a fixed rational-query recurrence.** `after_c5/extractor_width/direct_carry_extractor.py:emit_prefix` iterates 35 nodes and prior-head queries. Its shared `night_c27/arithmetic/raw_query_extractor.py:query_step` performs a fixed multiply, public scaling and swap. There is no 70-round syndrome-discrepancy update or 19-qubit tagged exception stack in this call path.
4. **There is already history reconstruction.** `after_c5/converter_width/tail_phase_defer/rolling_tail_deferred.py` erases a previous flag while retaining only its classical HMR outcome, then repays the phase at the existing return zero-query. `after_v3/k24/v5_transpose14/transpose14_core.py` similarly stores classical predicate debts, reconstructs flags at witnessed seams and repays them. The names “history” and “cache” alone would therefore be misleading indicators of novelty.
5. **Projective Euclidean machinery remains in a later subroutine.** The preimage converter uses recursive polynomial division and quotient frames, inherited domain restrictions on degree drops, and selected 17/14 windows. Thus “not the original EEA locator” does not mean “no Euclidean algebra anywhere.”
6. **The 24-output peak really is joint field arithmetic.** `inverse_v2_actual_eea_product_certificate.json` checks the actual 821 block at KMB indices 12,581,893–12,588,114: 99 CCX, 6,122 CX, 24 output-linear rank, and all 576 bilinear basis pairs. It computes `target ^= conjugate(left) * right` in GF((2^12)^2). The two 12-bit halves are not independent products that can simply be serialized.
7. **Generic arithmetic improvements are already present.** Rank-42 GF(2^12) multiplication, rank-99 GF(2^24) multiplication, a 66-Toffoli nested-norm inverse, and the 62-Toffoli quotient-phase provider are in the source. The latter already contracts the inverse into a phase instead of constructing a full inverse output. These are not new gains obtained by importing this paper.

## Unused ideas, practical candidates and rejection conditions

### A. History reconstruction for the current rolling flag: bounded source-level investigation

The specific BM invariant does not apply to this rational-query state. Its **method** suggests a focused question: can the one surviving rolling flag be inferred cheaply from the post-update head/carry state and temporarily erased across the 24-helper arithmetic?

Start with `RollingTail.begin_slot`/`finish_slot` and the pure classical rational-query reference. The existing identity is `zero(v/u) = f_previous XOR f_current`. It does **not** by itself reveal `f_current` after `f_previous` has been erased. A proposed decoder must exploit an additional reachable-state invariant; merely observing that the flag is not used inside a multiplier is insufficient.

Bound the first CPU experiment to 20,000 law-drawn trajectories, fixed seed, plus explicit zero/low-weight/degree-gap cases, at most 120 seconds and 1 GB. Record each public node's pre/post head, carry and flag; search for a fixed, low-cost zero/parity witness and report all collisions between equal proposed witnesses and different flags. This is a rejection-oriented screen, not proof of equivalence. If a witness survives, derive an algebraic identity on the admitted domain before emitting gates.

Reject a candidate immediately if it depends on inspecting a quantum value classically, fails a reachable-state counterexample, loses an HMR phase correction, or leaves another 889-qubit peak intact. Even a complete 889→888 reduction permits only about **861.105 extra mean Toffoli equivalents** at our current T and unchanged R. Reconstructing a long parity of zero tests on every multiplication is unlikely to fit that budget. No working witness or qubit reduction is claimed here.

### B. BM's omitted exception reconstruction: a separate architecture study

The author's detailed README derives a formula for retained discrepancies but chooses storage because saving 19 qubits costs about 7,700 Toffolis and worsens its TQ objective. Using those same approximate native counts, this change multiplies TQ by 1.00688 but Q²T by 0.99647. This illustrates an objective-dependent decision worth reconsidering in a BM research branch.

It is **not a drop-in 821 improvement**: our pipeline has no corresponding 19-qubit stack. Its cost must first be translated into Kickmix, its mask interface generalized, and its true global peak remeasured. A cheap initial gate inventory of the author's BM blocks should separate genuine three-quantum gates from promoted classical controls before attempting any full build. At unchanged Q=1,837 and equal R, a port would need mean official T below approximately 89,491.12 merely to match the current candidate's Q²T. Reject the wholesale replacement if a sound lower bound already exceeds that threshold.

### C. Phase-polynomial consolidation: keep as a separate follow-up

The paper's chemistry-controlled quadratic phase technique suggests symbolic consolidation of phase expressions across a complete small DQI cleanup block. However, current DQI already has direct cubic trace contraction and deferred phase debts. It would be incorrect to assume every CCZ is reducible by a quadratic-rank calculation. A useful screen must first prove the selected phase is quadratic in the chosen live variables, include all classical conditions and HMR corrections, and respect block boundaries. No phase reduction is claimed by this audit.

## Actions completed

Read the primary paper and article, downloaded and hash-verified the author's DQI text sources, traced the current production source chain, checked the actual-block certificate and local verification reports, and documented the differences above. No additional full simulation, score submission, source rewrite or candidate mutation was performed.
