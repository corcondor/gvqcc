# Native full circuit results — diagnostic, not a submission

Two whole competition-ABI KMBs were emitted locally, concatenating actual serialized SDK chunks in packet order, with all registers unchanged. KickMix 1.0.0 read the single full KMBs and ran the same three panels, ordinary 1024 / saved stress 622 / dense 144. All four error counters zero in each panel, both candidates; paired output differences zero. No official 102400 run. Gray128 complete artifact could not be materialized (project raw-byte permission); its known 316084.1416 value is a cited prior comparison only.

| Circuit | Q | paid | ops |
|---|---:|---:|---:|
| #341 original chunked diagnostic | 900 | 12823738 | 190791716 |
| coherent cursor scalar | 900 | 5853458 | 146691436 |
| coherent cursor + block products | 900 | 5217674 | 154461920 |
| variable degree + retained norm/AND phase | 900 | 4926929 | 149109755 |
| fixed degree 35 + self-tagged padding | 900 | 4998749 | 151594177 |

Variable raw SHA256 db94f7c871c65b216f5e54024c16c4da481fc19981f2d4f6059524b38022b032. Fixed raw SHA256 f23a952d17581baf59ffcfda7c3b46494eb796b98a6cb3cdcbe72303f22c4549. Whole KMBs and reproducibility archive delivered separately.

Packing: retire a valuation-v block (0^v,a,H1,...,H_(v+1)) as (a,H1,0,H2,...,0,H_(v+1)). Store the current boundary in six quantum bits, update h→h+v+1. On reverse, a nonzero first word identifies the prior active pair, and valuation equals cursor-h-1. Clear flags from the new encoding; no measured syndrome/history. Inactive predicates remain identity. Block convolution uses disjoint source banks, classical HMR debts, and guarded output shears. 

Squarefree completion: for distinct fixed anchors, multiply N,Q by (1+alpha X) if degree<35 and Q(1/alpha) != 0. The added factor is exactly the common root of N and Q at that anchor, hence no retained 35-bit flags; reverse recovers the flag and divides. The true roots are simple and have nonzero numerator. Native pad and unpad each 35910 paid, 1242211 ops; 223 legal cases across two seeds passed.

Root scan: keep the norm chain during root-conditioned trace contraction and erase it by HMR, retain four summary AND bits across phase, clean them by local debt. 166→95 paid per point, 679770→389025 all 4095 points. 151 all-weight and structured inputs ×2 measurement seeds pass each phase block. 

New 17-dimensional modular-square reference: reverse monic locator R of degree 2m+1 into Q=Qe(X²)+XQo(X²). If B is the reversed numerator and C=B/Q mod X^m, the odd coefficients of the reversed modular-square remainder are Bez(Qe,Qo) times the reversed coefficientwise square of C. Euclidean congruence for A=Bq+R: Bez(A,B)=Bez(R,B)+B(X)B(Y)Bez(q,1). 80 squarefree ranks, 512 Euclidean block certificates and 640 square odd-block identities pass in GF4096. This last reference is not native and is not part of the final KMB.

Lean 4.35.0 strict local proof: 18 declarations PASS, allowed axioms only, no sorryAx. https://github.com/corcondor/gvqcc/actions/runs/46178227445 . Whole serialized circuit correctness is sampled, not Lean-proved. We used packed Pade/continuants as an alternative to the proposed BM, not a new BM implementation. No score improvement vs Gray128, no main merge, no submission.