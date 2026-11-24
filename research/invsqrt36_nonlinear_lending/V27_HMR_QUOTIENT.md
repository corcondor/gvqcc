# V27: joint HMR measurement-basis quotient and global classical liveness

Research only — NOT SUBMISSION, no main or Kaggle mutation. Exact native diagnostics; full width remains 37Q, no expected paid-gate or official score increase. Parent PR73 head 2b803013e24db25b7c881e745dc2d45586f74866. Historical four ANGLE archives remain unrecovered; no exhaustive novelty or world-first claim.

## Actual recovered/verified native portfolios
| track | V26 | observation bundling | single-HMR dressing | joint HMR quotient | classical liveness | expected paid | final full-occupancy cuts |
|---|---:|---:|---:|---:|---:|---:|---:|
| low | 56734 | 56694 | 56652 | 56593 | 56145 | 22501/16 | 7504 |
| joined closed-priority | 53049 | 53042 | 53006 | 52975 | 52536 | 22725/16 | 5785 |

Parents SHA256 8db1710226832911e0499238017e4f572033ec37ccd8546d7183587b092abb97 and 1e435078033c533b9fece7d949af1c43540615f618b9c6ee9aae4fa777bc066e. Final SHA256 low edaa65636e85bb778bd23f6701685854c5fb06f76c0c672465ca8a4b11771fc3, joined 148fe153e90f245df798854da264b677f6379b6dc193f1aedb78ee9ee06fb6c2. Exact 3,133,452 legal inputs, 1276/1289 independent potential HMR outcomes, 55 rotations. Phase receipts and independent serialized edit-chain, classical guard, terminal/cost/width replay PASS. Not official verifier or whole-circuit Lean proof. Source full cuts 7519/5764: final counts not directly comparable to true mapped width relief, joined count increases by 21.

## Mathematical/implementation changes
1. Nonzero global observation bundling: same unweighted quantum monomial, multiple classical guards; replace with one actual existing guard if exact phase sum agrees. Low 629 proposed/60 pass, 40 commands saved, max 4466; joined 313 proposed/7 pass, 7 saved.
2. Dressing: HMR(q) with outcome m gives phase m*q and resets q. Inserting CX from surviving affine d before HMR adds m*d with no data/classical outcome change. Delete remote phase terms iff their phase XOR equals m*d. Sample affine quotient at the original HMR cut; pair/triple/Gaussian dependencies, exact BDD acceptance. Low 346 tested/39 pass, 38 disjoint, 77 phase commands removed/35 dressing commands added, max distance 34928. Joined 321/36 pass, 35 selected, 71 removed/35 added, max 22263. No paid savings.
3. Joint direct sum quotient: a guarded phase with linear SSA guard XOR_j m_j contributes its unweighted monomial to each measurement-cut quotient W_j. Sparse elimination of vectors in direct sum over W_j yields candidate joint premeasurement dressings; verify the actual accumulated phase exactly, not merely samples. Low 10057 eligible observations (657 multi-event), 769486 elimination steps, 776 exact candidates/22 pass, 65 removed/6 added. Joined 10011 (654 multi-event), 765445 steps, 542 candidates/8 pass, 34 removed/3 added. One genuine multi-HMR group per track. Low actual HMRs 7812,8167 with record 519,539 and CX(15,35) at both; removed phase ops 26107,27181,27261 on v27_low_dress SHA 0a1c1cff... . Source-to-consumer span 19449. This is a distinct transformation from PR73 zero-relation deletion, deferred data and PR61 phase dictionaries; no historical universal novelty claim.
4. Classical liveness: remove 401 no-op+47 dead writes low, 380+59 joined. Symbolic all-history check of every surviving nonclassical activation/scope and final classical records, 55423/51834 comparisons. No paid or HMR changes.

## Carry module and negative results
Mapped all 60 PR71 source chain links on both V26 parents by independent sample. Low actual 17 nontrivial chains/77 HMRs: replace each old carry measurement except last with c_i XOR c_(i+1), use n_i=prefix XOR(m_0..m_i) and recover m_i=n_i XOR n_(i-1). Full-domain compositional serialized replay PASS, 77 source blocks/20 phase positions, sign debt zero per chain, triangular bijection, 1276 independent HMR. No terminal correction needed when last carry measured unchanged. 56694 -> 57035 commands (worse 341); reject. Classical cache variant zero positive groups on already compressed V26. Guard-split paid search 1,483,538/1,498,586 sampled branches, 954/944 exact failures. Two-update rank-one nonlocal resynthesis up to 1024 native ops: 43,188/45,316 pairs, 71 exact candidates each; all fail (69 endpoint, 2 rotation). New width re-screen low after liveness: 3373 proposed, 1138 second-sample pass, 36 distinct prioritized candidates exactly checked, all fail (31 data, 5 endpoint). Earlier unfiltered exact width replay hit time cap. No complete36Q or paid gain; do not count sample-only links as proof outside the actual validated low rebase.

## Score model (PR43, NOT official)
At E=1406.3125, 37Q 33.17031641, hypothetical36Q 33.47464823, extra E budget <45.74140236. At E=1420.3125, 37Q 33.07684213, hypothetical36Q 33.38031635, extra budget <31.74140236. Because command count is not an input to this model, these predicted scores are unchanged by V27.

## Lean
V27HMRQuotient.lean: guard distributivity, HMR dressing, joint absorption with explicit semantic premise, prefix/recover inverse, carry telescoping, concrete resource counts. Actual reachable premises checked in Python BDD, not Lean. CI configured using Lean 4.35.0. Companion conversation ZIP contains native sources, scripts and receipts.

## Literature used and scope
- Gidney (2018), https://doi.org/10.22331/q-2018-06-18-74 — measurement erasure and correction; implement altered measured Boolean coordinate rather than new paid uncompute.
- Amy & Lunderville (2025), https://doi.org/10.1145/3704873 — relational analysis of phase including classical control; use versioned affine guard SSA and quotient relations across HMR.
- Kornerup, Sadun & Soloveichik (2025), https://doi.org/10.22331/q-2025-02-18-1636 — measurement phase debt/pebbling; explicitly track phase debt across large time spans, not merely data equality.
- Luongo et al. (2025), https://arxiv.org/abs/2407.20167 — MBU of arithmetic; carry-chain measurement basis as concrete variant, not reproduction of reported modular-adder savings.
- Cuccaro et al. (2004), https://arxiv.org/abs/quant-ph/0410184 — carry recurrence.
- Boyar & Peralta (2010), https://www.nist.gov/publications/new-combinational-logic-minimization-technique-applications-cryptology — linear factoring/guard network comparison.
- Bryant (1986), https://doi.org/10.1109/TC.1986.1676819 — exact ordered decision diagrams for symbolic history acceptance.

No external paper's implementation was imported directly; connections are algorithmic applications, not claims of reproducing their performance. Other-session coordination through PR71/73 and recovered archives. No further score/width claim.
