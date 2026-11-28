# Direct 316K lineage: joint-norm and low-rank pad rebase

Research only, not submission. The exact original frozen donor SHA256 4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52 was rebuilt. All candidates use #261's exact prelude and physically replace its nonlinear decoder; no host-selected syndrome branch.

- Joint norm: 75 rather than 79 paid per nonzero field point, 527468 static paid, 79569516 ops, 900Q; 996 forced plus 1024 ordinary native executions zero all four errors.
- Low-rank padding rebase: 389593 static paid, 63476208 ops, 900Q after physical splice (890Q core); 996 forced plus 1024 ordinary native executions zero all four errors. Distribution mean 388453.0400390625, stress mean 359066.1435742972 (different panel, many zero masks). Final SHA256 a74dbc8482da1d0975f760a97eb5a7e81863cab74fc65891b50009aa61af590b. Independent ordinary panel, not an unchanged official score run.
- Static improvement relative to #261: 154255 paid. Still not below 316000. The ordinary samples are not matched to #259's earlier ordinary panel.

## Mathematics and limitations

A 72-case native raw-key profile found squarefree padded D and the expected weighted rational values. For weights 0..5 the observed half-Euclidean maximum degree gaps were 13,13,9,9,5,5. The existing converter excludes gaps >2. Common factors are not themselves the obstruction. Replace low-weight padding G_w by G'_w, selected coherently via irreducible marker factors. For D=G_w d and N=G_w n, the replacement preserves N/D at nonpoles and the physical residue N(a)/D'(a) at all simple nonzero physical roots, since padding is nonzero there. Distinct low-dimensional polynomial subspaces G_w F[X]_{<=w} and G'_w F[X]_{<=w} are exchanged by controlled swaps in a shared constant linear basis; no dense controlled matrix is needed. Undo flag using the new marker. This changes the native full decoder rather than applying a residual repair to its output.

All twelve sampled low-weight post-rebase half-Euclidean profiles had max gap 1. This is empirical, NOT a proof of the gap bound for all legal inputs. The old pad lists were inferred from measured key outputs; their full legal-input classification and gap-safe converter remain unproved. Do not claim universal correctness or submit on these receipts.

## Reproduce

Use the exact environment and pinned dependencies in #261 README. Copy kernel_joint.py to /tmp/seam. In the team directory, copy core_direct.py to core_joint.py and insert 'from kernel_joint import kernel' immediately before its final main guard; then run core_joint.py /tmp/seam/core_joint.kmb. For the independent low-rank rebase candidate copy core_rebase.py next to the unmodified core_direct.py and run core_rebase.py /tmp/seam/core_rebase.kmb. Use the #261 splice_direct.cpp with the exact donor, and verify_raw.py for 996 cases; for the ordinary panel use #254 verify_distribution.py and its fixed seed, with the official verifier module in PYTHONPATH. Both candidate receipts give exact hashes and command IDs. No main merge, Kaggle submission, or new Lean execution claimed.
