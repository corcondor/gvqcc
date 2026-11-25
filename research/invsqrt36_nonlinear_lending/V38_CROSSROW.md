# V38 — cross-row carry transport and verified PR94 transfer

Research only / NOT SUBMISSION. Stacked on PR96; its corrected Lean CI passed run 45556808799. V38 uses two separately pinned parents and does not mix cost or occupancy metrics.

| parent / candidate | native ops | expected paid | all-nonzero cuts |
|---|---:|---:|---:|
| PR86 | 51024 | 23077/16 | 3702 |
| V38 all-carry | 50440 | 25349/16 | 3250 |
| V38 budget +9 | 50988 | 23221/16 | 3650 |
| PR94 | 41935 | 23127/16 | 3239 |
| V38 PR94 donor | 41760 | 25319/16 | 2809 |

- PR86 SHA d873f84acb4a9afb5652f7f56597728953beb60d91afdb7262a6a4249e9f8274.
- V38 all-carry SHA 1e5c88a8101b97b499bebeeb039ab640d0acb5cc91dac85f41ab6741b45d09f5.
- V38 budget SHA 7c85e201c23d4480d5098523b3691b30ed3b9345db98eb15b8cdf8fdaf9cf6c6.
- PR94 SHA 2a4689fc1316ff43ff61002149e2a9e6f9b54239ba4e9c121f282423a17aeabd.
- V38 PR94 donor SHA 51d20041a28d45a175d9aa2cba372e8086b0841e18d16911730b0a143802920b.

## Physical fragment and all carry motifs
PR86 [7402,10000), 2598 -> 2006 commands, 193 -> 333 static paid, 166 source HMR records, 136 exchange motifs, no q36 reference; header 36, SHA 4ebfe0bfff2233ccb326dadce6d0ba669b4d7df27585da1059ce16c449b4a14f. Fragment is NOT standalone oracle: valid on actual entry states and pre-existing records. Special terminal 6-exchange row [7747,7840), borrowed cubic bridge [7689,7747), in-place factor bridge [7843,7901). Complementary factor identity replaces five-paid dirty bridge by three-paid bridge; saves two paid against intermediate, costs +1 vs source. Phase dictionary HMR532 7 -> 5; HMR540 6 -> 0, retaining source event in same-parent replay. The original 161 motif blocks comprise 23 whose four commands already do not reference q36 and 138 with q36 references. The latter are 136 in the contiguous fragment plus two disjoint verified replacements [7087,7092) and [26972,26977). This is not a claim that all surrounding computation uses 36Q.

19-row incremental fixed chart 1620 ops vs alternate carrier 1616, both 278 paid; prior individually compiled 1916 ops. 2612 chart patterns, 733 beam row-boundary trials, 41034 sampled affine CCX reset tests (zero fits), 47411 simple two-paid deletion trials (no fits), broader 50889 pair-repair trials (one sampled candidate, superseded, not counted as exact gain). No direct reverse/forward CCX deletion. Safe shared-factor and commuting linear compaction. 53-candidate interval DP, budget +9 selects 3 disjoint verified groups.

## Exact replay
Ordinary accumulated phase BDD exceeded memory; new verifier expands each measured phase into ANF using P=low xor m*(low xor high), retaining full legal-domain bit masks per monomial. Both serialized KMBs reread; exact source HMR events aligned, phase coefficient maps equal per replaced interval, data/rotation/stack/active/classical state equal at boundaries, unchanged gates identical. All three final candidates PASS on all 3133452 legal inputs with respectively 1281,1281,1276 independent HMR variables. 142 nonzero ANF phase coefficients in long group. PR94 [6599,8784) -> 2010 ops: 13 entry and 9 exit adapter possibilities, 117 sampled tests, 54 pass, best has 4 affine adapter operations; replace source-removed HMR540 by classical reset in donor, exact replay PASS. Full peer peak37Q. All-nonzero cuts are a width-pressure metric, not a proof of minimum achievable width.

## Literature and proof scope
Cuccaro et al ripple ladder; Khattar/Gidney conditionally clean ancillae (borrowed factor, restoration); Amy/Lunderville phase folding (per-record phase dictionary/ANF comparison, not a full implementation of their algorithm); Remaud/Vandaele ancilla-free adders (inspiration for alternate majority carriers, not reproduction). Recent reaction-depth and QFT/ripple work surveyed at abstract level only, not implemented due to gate-model mismatch. V38Crossrow.lean proves finite bridge and carrier identities and arbitrary-length Abel transport by list induction, not complete circuit verification. Native scripts, full receipts, and binaries in reproducibility archive in chat.

Complete oracle remains 37Q, no official verifier, no score improvement claim, no main or Kaggle changes. 80 long-range product reuse and zero-overhead cross-row nonlinear fusion remain unsolved.
