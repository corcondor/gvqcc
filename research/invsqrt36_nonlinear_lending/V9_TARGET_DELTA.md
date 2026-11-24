# V9 target-delta integration (research only)

## Exact parents and result
PR45 (f7abc033dbed5477d5685225d9bf5fe262ceb888189ebcc3266ce23f9d15fd6d): 42599 native instructions, 1875 static paid, 1704.3125 expected paid. PR48 (90a798c0995a3ed1fece0aca556bcd0dd8b9c6ecd9f30fadd9b79022734f4f9e): 42622 native instructions, 1867 static paid, 1696.3125 expected paid. Reconstructed PR48 from exact PR45 native list and eight PR48 gate-list donors, and required byte-identical SHA256 before composing the two disjoint universal edits.

V9 integrated: SHA256 67ba0273bc086f25ab91cbb1b287cff7d16aaec2addaa4d59a63a08c6a61fd79; 42624 instructions, 1865 static paid, 1694.3125 expected paid, 55485/60766 covered source ops (91.3093%), remaining 5281. Peak remains 37Q. HMR 1174; 55 rotations. No new official score, no full36Q, no new full BDD run. Local exact BDD on PR45 accepted two edits; independent all-state ANF certified both lists; PR48 exact bytes and disjoint splice checked. PR48 reports complete symbolic replay for eight conditional donors. The new universal equalities compose with that prior certificate, not a claim of a freshly completed full BDD run.

## New target-delta search
Unlike PR45's stable-control multi-target grouping and PR46's single-gate affine cofactor, group commuting same-target distinct-control updates with identical versioned guard, respecting existing chart boundaries. Search affine and rank-one factorizations with one/two-coordinate parity factors on legal sampled states, then retain universal exact ANF candidates. PR45: 8928 commutation checks, 26 families, 32760 factor probes, 2 sampled/2 universal accepted. PR44 wide: 7645 commutation checks, 35 families, 44100 factor probes, 2 sampled/1 universal accepted. Width branch separately: 47094->47095 ops, 1914->1913 static, 1727.3125->1726.3125 expected, 55829/60766 covered, SHA256 c1d706a1f0f1533bc02565f9f95e1220f79ab0208577f48c2152089bfe5d5d26. Do not add the width branch's gain to cost branch.

Actual PR48 intervals [11262,11264), [13624,13628) each save one unconditional CCX with two/four original operations respectively. PR44 interval [16993,16997) saves one unconditional CCX. All three local gate lists are reproduced in lean/TargetDeltaV9.lean; no entry-state assumptions in the new proofs. The archive contains the pinned KMB inputs, search code, exact ANF check, replay and integrated output. Lean CI is required for formal certificate acceptance; whole-oracle verification is separate.

## Literature (related methods, not claimed inventions)
- Riener, Exact Synthesis of ESOP Forms, https://si2.epfl.ch/~demichel/publications/archive/2019/Riener2020_Chapter_ExactSynthesisOfESOPForms.pdf
- Scaling-up ESOP Synthesis (2019), https://people.eecs.berkeley.edu/~alanmi/publications/2019/ismvl19_esop.pdf
- Jung, Dalmeijer, Van Hentenryck, A New Optimization Model for Multiple-Control Toffoli Quantum Circuit Design (2024), https://doi.org/10.4230/LIPIcs.CP.2024.16
- Papakonstantinou, Systematic Synthesis and Optimization of Reversible Quantum Circuits via MINLP, Toffoli Permutation, and Local Search (2026), https://doi.org/10.3390/quantum8030079
- Improved circuit synthesis approach for exclusive-sum-of-product-based reversible circuits, https://doi.org/10.1049/iet-cdt.2017.0016
- A multi-commodity network model for optimal quantum reversible circuit synthesis, https://pmc.ncbi.nlm.nih.gov/articles/PMC8219173/

Conditional score model inherited from PR43: 31.43521543 at 37Q, hypothetical 31.72362801 at 36Q; to beat reference requires E<1452.05390236 at full36Q, i.e. >242.25859764 further expected-paid reduction, other task and rotation costs fixed. No official verification or submission. Main untouched. Do not repeat this exact family search with merely larger sample counts; next priority is arbitrary affine-coordinate transport and width/paid tradeoff on residual arithmetic, not individual CCX repeats.
