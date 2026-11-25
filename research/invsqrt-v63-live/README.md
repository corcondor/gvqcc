# V63 live chart joint transport — NOT SUBMISSION
Parent PR147. Separate from PR152's spectral oracle. All native new circuits <=36Q. Not full inverse-square-root or official score.
| Variant | Q | E paid | ops | successor products |
|---|---:|---:|---:|---:|
| V62 |36|928|7822|17|
| V62 |35|1132|7834|17|
| 17-bit chart global |35|776|6541|17|
| modular chart global compact |35|760|6212|17|
| modular chart global |36|913|6506|51|
| modular chart global |36|1149|8383|136|
Matched logical first Horner digits and successor bit products, not identical internal encoding. All 3,133,452 legal inputs, independent HMR sign coefficients and restoration PASS. Global optimizer preserves every pinned readout; dynamic 35Q remap preserves all source cuts modulo mapping. 13-bit modular reflection plus no-borrow flag replaces 17-bit chart. Coefficient and high-word reconstruction on demand; 240 fused cell states, 384 coefficient table states, 67,108,864 local modular pairs exhaustively checked. Address search 1129 charts/663 dictionaries with nonmonotone edits; no optimality claim. Restricted fixed-union and nonlinear decoder searches failed. Q35 compaction of pre-resynthesis modular k3 failed at op3710. Full successor accumulation, rest of Horner and terminal phase not implemented. No official verifier, submission, main or score mutation.
Final Q35 SHA256 c1c3655cbb593e7c322fec1aea4c3188090aec85c8e8f37f7437d3070d2f1424. k3 Q36 e15be3a42015e71e9d169a22b9ae58d8d4ab886d21aefacdd7139b81f45fb675. k8 Q36 a46890951a47f34d387fd58bcfa5ffadd036136f639c83318122b6814718a65b.
Full 226-file executable archive GVQCC_V63_LiveJointTransport_NOT_SUBMISSION.zip SHA256 b15dd427eb03cdcc2fad423490340ddbc26bc417ef6138e957845ea9840f1cbd (delivered in conversation). Reproduction README_V63.md. Local Lean identities, not whole native proof; local Lean unavailable.
References: Gidney arXiv:2507.23079 (constant workspace adder); Yang et al. PRA 113 052443 (2026) doi:10.1103/6vm9-21gr (shared multivalued decoder factorization); Bandyopadhyay et al. Quantum Rep. 8(4) 111 (2026) doi:10.3390/quantum8040111 (reversible embeddings/bounded synthesis). OpenAI Nov24 Fourier/matrix preprints are finite sharing inspiration only, not asymptotic algorithm port. 
