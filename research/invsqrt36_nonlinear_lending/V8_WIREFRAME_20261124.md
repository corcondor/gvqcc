# V8 physical-wire frame / peer integration (research only)

Source reference 6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03. Parent PR #43, 2e5a30bc77cb80e4aa820d029ac5133cc8763699. Other sessions: #40, #41, #42. Main remains untouched.

## Actual results
- V7B native SHA d6c6e0006165b88f615f33b29f95abe468aaef6412ea92c4a01f1a95dd6f05a3: 8 CCX replaced by reachable affine parity; 44 candidate edits, 36 rejected incl. six width gaps. 1894->1886 static, 1718.3125->1710.3125 expected, 50015->50038 ops, same 55184 source coverage. Candidate 1ad59873b86ecd82fd11ade73e43f12405172ae386a45fa89fc2b036bf2a0988. Exact BDD endpoint comparison for every accepted edit on all 3,133,452 legal x / 1168 potential HMR events. These gate-level decoder identities are formalized conditionally in WireFrameV8.lean.
- Independent peer archive GVQCC_V7_Integrated_91pct_NOT_SUBMISSION.zip: verified parent 97623d3bb9b7fb61aeabd7312e869ab64e49da9c4070d359e79d86688c9161a5 (55485 source coverage, 5281 residual). Imported PR42 only at unique exact sequence match native [42532,42611), 2 CCX saved, 63035 whole BDD comparisons. Applied rankhub compiler: 173016 search trials, 1622 selected epochs, 36090 exact checks, 63144->50051 ops, 1898->1892 static, 1717.3125->1716.3125 expected.
- New physical permutation frame: virtualize only unconditional SWAP outside guarded scope, remap all later operands incl HMR and Z_POW, reconcile at chart/gap exit. 2757 virtualized, 587 restored; 50051->47881 ops. Exact per-operation comparison in moving permutation for all 50051 original operations; 3,133,452 legal inputs / 1174 independent HMR variables. Whole candidate SHA a5199593e674dbd8e50a03aecd6dc00d44aa7213c899cd7e84c2664e86cd47d5. Static/expected paid unchanged by this pass. Conservative scope-fenced dependency depth 45290->34545 relative to peer parent; not hardware time. First attempt at full-chart phase accumulation exceeded process resources; use per-op comparison instead.
- Reachable cofactor pass on peer+frame actual circuit: 1782 CCX, 44 CSWAP, 66 CCZ screened. 49 two-sample candidates, 8 exact accepted CCX, 41 rejected. Actual serialized 47904 ops, static 1884, expected 1708.3125, 55485 coverage (91.3092848%); SHA 59e705ddab9f65048e570f12f168da1d83ed3e54d5a482a7bb3088f815d3bf65. Do NOT add the separate V7B 8 removals again.

## Budget
Conditional model: cost Q*(expected_paid+240.37798500105055), other tasks fixed. Baseline 33.17031640530013 and invsqrt cost 60927.54794503887. At 36Q require strictly less than 1452.05390236114 expected paid. 1708.3125 needs >256.25859763886 additional reduction. Hypothetical width-only score 31.6474745365, not a gain. Whole circuit still 37Q; no official verifier, no competition score, no Kaggle submission.

## References and code (independent implementation, no claim of external fork)
- DeCross et al., Qubit-Reuse Compilation with Mid-Circuit Measurement and Reset, PRX 13 041057 (2023), https://doi.org/10.1103/PhysRevX.13.041057.
- Hua et al., CaQR, ASPLOS 2023, https://doi.org/10.1145/3582016.3582030.
- Paler, Wille, Devitt, Wire recycling for quantum circuit optimization, https://doi.org/10.1103/PhysRevA.94.042337.
- Fang et al., Dynamic Quantum Circuit Compilation, https://arxiv.org/abs/2310.11021 ; https://doi.org/10.1109/TC.2025.3643826.
- Rovara, Burgholzer, Wille, Qubit Reuse Beyond Reorder and Reset, https://arxiv.org/abs/2511.22712.
- Benbetka et al., Mapping Dynamic, Hierarchical Quantum Circuits, https://arxiv.org/abs/2609.08075.
- Solar-Lezama, Program Synthesis by Sketching, https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-176.html.
- Abate et al., Counterexample Guided Inductive Synthesis Modulo Theories, https://doi.org/10.1007/978-3-319-96145-3_15.
- Amy & Lunderville, Linear and Non-linear Relational Analyses, https://doi.org/10.1145/3704873 (previous reference retained).
- QAOA inspiration https://arxiv.org/abs/2503.09356; no QAOA execution in V8.
- DeepMind formal verification: https://github.com/google-deepmind/formal-quantum-computation.
- Qiskit ElidePermutations (established virtual-permutation technique): https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.transpiler.passes.ElidePermutations ; https://github.com/Qiskit/qiskit.
- Qubit reuse implementation https://github.com/qiskit-community/qiskit-qubit-reuse (Apache-2.0).
The novelty here is applying cross-measurement permutation frames to the existing GVQCC physical-chart ABI, not inventing permutation elision itself. Complete sources, donor gates, serialized KMBs and receipts in separate research archive.
