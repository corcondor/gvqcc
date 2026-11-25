# V64 — modular affine tour and truncated successor stream (NOT SUBMISSION)
Parent PR156, separate from PR158. Actual <=36Q partial KMBs, all 3,133,452 legal inputs, independent HMR coefficients, input/work restoration and logical readouts PASS.
| variant | Q | E paid | ops | products |
|---|---:|---:|---:|---:|
| k1 |35|742.5|5924|17|
| k3 |35|817|6188|51|
| k8 |35|968.5|7040|136|
| k10 |36|999.5|7193|170|
| independent inverse k17 |36|2136.5|12679|289|
| affine tour k17 |36|1866|12193|289|
| keep13 guard11 |36|1668|11024|155|
| keep14 guard12 |36|1675|11053|160|
| keep13 guard10 |36|1682|11117|166|
Last three also check weighted sums of readouts in classical replay, not physical accumulator. Exact model: 60 sampled configs, 12 all-domain checks, 7 pass with >=50m integer margin. 155 margin 54097941 ratio .94369838; 160 margin73367299; 166 margin81961327. No final native oracle. p=m*T+floor(m/2), L=p mod8, q=floor((p+4)/8), y=q-floor(L/4). For odd m, t0=(L-floor(m/2))*inv(m) mod8, c_m=floor((m*t0+floor(m/2))/8), y=m*(T>>3)+c_m. In-place modular transition m_b*z_b=m_a*z_a+c_a-c_b. Tour over odd coefficient coordinates instead of independent inverse/restore. Exact care mask tour 53249 DP states/92 edge masks, off-care closure paid explicitly. Save highest two offset digits in retired multiplier wires. Finite search, not optimality.
Q35 k8 SHA fba7431412f4eef18692315c5b844b9fc16cb3eb0f37e072a3d714c595149775; Q36 k17 SHA 749e616f4a43df321c4c0b9338ff69d32e3585e838c2ab5b6a8eebb07611a82d; 155 SHA d45dc97ab68ac4e4d940c6b3d7e138b0ac79d94219f55060252daf8015aefbb5.
Archive GVQCC_V64_ModularAffineTour_NOT_SUBMISSION.zip, 374 entries, SHA256 7c4c6b86110124f2a818f232755fa569b131c1aa2e2d11db93436a6a310c173a, delivered in research conversation. All sources and receipts included, exact reference table regenerated, reproduction script supplied but full archive reproduction not rerun. Lean local identities only. PR156 local Lean CI success run45694913687. PR158 k1 E729 better; PR155 standalone MAC uses 68 wires, not directly composable. Full budget at 36Q is E+T/4<1692.432, 155 stream E1668 leaves only 24.432 before downstream. Do not submit. No main/Kaggle changes.
References Gidney arXiv:2507.23079; Luongo et al. arXiv:2407.20167; Halpenny et al. arXiv:2611.26605 (Fourier basis not ported); prior OpenAI predictor/repair and finite tensor-sharing ideas (not asymptotic port).
