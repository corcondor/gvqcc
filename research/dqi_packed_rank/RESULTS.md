# Coherent packed rank/continuant extension of PR340 (research only)

Base: exact PR340 head 85471053eaf9b50aec9c715bb281f300806c09dd. No merge to main, no submission.
PR340 is a verified classical Gray72 selector reconstruction, not the recovered historical 316084.668 KMB.
Inventory: 337 retrievable PR titles through #340; #14, #118, #163 return 404. Selected related bodies, diffs and CI inspected; not a claim of reviewing every line of all 337 PRs.

## Integration
- #208–210, #232, #334, #339: ghost/low-weight cases, rank = sparse support, exact residual.
- #284, #287, #303, #304, #329: in-place Frobenius reciprocal, tower norm sharing, packed adaptive Pade, backward continuant.
- #335/#336: singular degree profiles; #293/#332: HMR repayment; #338/#340: phase-only dual/frame transport.
- Current standalone phase path uses direct rational residues, not the Gray72 selector.

## Local native receipts (KickMix 1.0.0, Python 3.13.5)
- Initial per-stage extractor: 144 inputs, 2 seeds, 900Q; forward 11450234 paid, inverse 11442846; rank XOR and history only.
- Blocked rank+N/D: 288 inputs x 2 seeds, all weights 0..35, 24 serialized and reloaded KMB chunks; 900Q, 0 errors. Forward extraction 3385718, unpack 2693654, restore history 2693654, unextract 3378330 paid. Rank target is arbitrary dirty; inverse restores syndrome and retains the XORed rank.
- Raw S0..S69, E0..E4094 end-to-end diagnostic: 151 independent inputs (72 stratified and 79 structured), 2 seeds, 32 serialized/re-read KMB chunks on one simulator per seed. 302/302 correct values, workspace, mask and phase. 900Q. Paid by mode: extract 3378330, unpack 2693654, phase 679770, restore history 2693654, unextract 3378330. Total static paid 12823738, total ops 190791716.
- Companion archive GVQCC_PR340_PackedRank_RawPhase_RESEARCH.zip SHA256 046ee0d9e0e9fd5d501c8186c34605294592753b5acd4ad15ffe893dab495d36 (delivered separately in research conversation). Includes actual native builders and #303 dependency sources, small KMB examples, full per-chunk SHA256 receipts, reproduction commands. Native sources are not fully embedded in this repository PR. CI here checks independent algebraic reference and Lean, not full native KMB.

## Exact equations
For legal moment series F=N/D, D(0)=1, order v, leading coefficient a:
F=a*z^v/(H+z^(v+2)*F_next). Retire exactly 2(v+1) coefficient words. Coherent path h->h+v+1 yields terminal degree, which equals rank by #339. Block reachability markers are reversible; prefix seeds are uncomputed. Backwards continuants: N=a*z^v*D_next; D=H*D_next+z^(v+2)*N_next. Implicit constant term D0=1 saves one field word. At nonzero root x, e=N(1/x)/D'(1/x); use original public binary mask and measured phase product. Traverse all 4095 positions with shared multiplicative frames returning to identity.
Effective nonzero pivot is 1+on*(a+1) on legal branches.
 
## Limitations
Not competitive: >12.8M paid vs Gray72's reported ~316k. Static cost vs previous mean is not a matched score comparison. No historical Gray72 physical splice, no single-file full KMB, no official score, no all-input end-to-end Lean proof. Preserve existing benchmark. Main bottlenecks are repeated coherent prefix reachability and suffix reciprocal, not anchor search; prioritize persistent degree representation and transposed block products from #284/#303/#336.
