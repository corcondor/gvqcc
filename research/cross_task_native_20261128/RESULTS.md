# Cross-task native affine audit (research, not a submission)

Pre-existing results from #77, #104, #157, #166, #213, #293, #297, #299, #302, #303 and #304 were screened for transfer to all three tasks. This PR is branched from #304 for provenance, but the exact #304 full tape was not recovered. DQI uses the separate 318072-static scale_guard donor. Chemistry and InvSqrt use the exact #292 audit non-DQI portfolio; no claim that #304 is integrated.

| Task | Old instructions | New instructions | Paid static old/new | Matched evaluation |
|---|---:|---:|---:|---|
| InvSqrt | 49825 | 40215 | 1507/1504 | Official 3133452 shots each, PASS; same cost 60865.11093368975 |
| Chemistry (15 ANGLEs) | 395524 | 385275 | 3267/3267 | Official 78016 shots each, PASS; same cost 247630631.38401353 |
| DQI (900Q) | 67457167 | 67189364 | 318072/318072 | Independent paired replay: 1024 ordinary zero errors, 576 stratified 279 union errors unchanged, identical flags and executed paid counts |

Official matched seed 20261128305, invsqrt batch 196, shots-per-x 1, KickMix 1.0.0. Not the full 64 repetitions per x. DQI replay uses the pre-existing same-input measurement seed 294293; not official 102400. No submission or score improvement. No private salt or hash selection.

InvSqrt: original SHA 2fef265d072fcb1b3b3f136d3bcf2b4b038baf3b5e4ea8b6de484f9747cb97ec; new SHA e1bb02c89581f32c895735131287ca355ee516b840429129cc014e2260fdb6fb. 801 exact affine intervals and 3 provably inactive CCZ. Average Toffoli 1404.623930731985 unchanged. All 33 generic-angle predicates exact over the legal cube; fixed-predicate max-absolute-margin LP found no better integer margin; eight individual zero-angle constraints infeasible on tested subset. No alternative angle circuit adopted.

Chemistry: 1008 exact affine intervals over all 15 circuits, NPZ unchanged. Full matched cost and lambda_eff=46.91426586893913 unchanged. 9315 pairwise orthogonal rotations screened, no improvement. Joint skew tangent LP timed out after four of nine groups; not a full certificate.

DQI original SHA b7474d2fa0a061da8666536a4a8bcba1fcbf377b4aac4615426d4819e77f59bd; new SHA fe7e93e0cef3f06c6471f47137bcc7b9b82641e971da0f22dd825206fea6b8c5. 68916 changed blocks, 271165 distinct matrix checks, 508917 cache hits. Every affine replacement exactly checked; unchanged guards and all phase/non-affine gates. Ordinary expected 316111.234375 unchanged, stratified 272 value and 151 phase errors overlapping (279 union). No error repair. #304's separate full 317996 candidate not accessible here.

Artifacts and complete replay receipts in the conversation research archive. Sources in this PR provide the general guarded affine pass, local Lean identities and results. This is an instruction-reduction result, not a competitive improvement. Never merge or submit as a repaired DQI.
