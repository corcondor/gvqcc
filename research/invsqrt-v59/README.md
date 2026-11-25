# V59: 23-active packed normalization and native in-place small multiplier (NOT SUBMISSION)

Parent PR139 and PR132; PR138/140 weighted-phase approaches remain distinct ABIs. No main or Kaggle changes. Every emitted candidate here has physical Q <=36. No full phase oracle or official score claimed.

## Verified native results (all 3,133,452 legal rows, serialized replay, restoration and independent HMR phase coefficients)

| Component | Q | Expected paid | Scope |
|---|---:|---:|---|
| normalizer care-set | 26 | 232 (from 238) | roundtrip |
| normalizer care-set | 28 | 180 (from 190) | roundtrip |
| normalizer care-set | 32 | 169 (from 173) | roundtrip |
| packed normalizer | 30 | 228 | roundtrip, 23 active at snapshot |
| packed normalizer | 32/36 | 217 | roundtrip, 23 active at snapshot |
| first canonical product | 36 | 497 | normalize + coefficient load + multiply + inverse + unload + restore |

First-product KMB: 3558 instructions, 492 CCX, 228 HMR. SHA256 9af76db829212b9589e707b191dbdf8b894f0288307c20c26ec39b68b6fa425f. Forward 132 CCX, inverse 132 CCX, coefficient load/unload 8 each. The compiler was regenerated and replayed from a separate directory, reproducing exactly the same SHA. No rotations. This is not the full Horner computation.

## Packed input and consumer ABI

s=10-floor(log4(x)), U=4^s*x. Store h=[s>0], tag tau(0)=0, tau(1)=1, tau(2)=2, tau(s)=4(s-3) for 3<=s<=10 in the low 2s known-zero bits. For h=1, bit0 -> s=1, else bit1 -> s=2, else s=3+bits[2:5]. High bits unchanged. Only 23 active wires at the packed snapshot; all remaining 13 wires are zero in the Q36 variant. This is not a claim of a full Q23 physical circuit.

Small multiplier: m positive four-bit, carry c<m, input b. u=(c+mb) mod16; o=b XOR [u>=m]. Then z=16o+u=c+mb, next carry=floor(z/2)<m. Shift in-place; reverse using b=[z>=m], c=z-mb. 240 valid local cases exhaustively checked including native forward/inverse/HMR. Each cell uses seven CCX controlled addition, four CCX overflow comparison and free swaps; measured carry erasure is corrected before changing controls.

Selected approximation: F32, B35, 24 segments, z=[2,3,4,5,14], k=[17,17,17,12]. C4/2^14 is in {0,1,2,3,5,8,13}. Use reserved code 15 for zero coefficient. At snapshot 1727, T wires 5..16 and carry wires 27..30 hold m_eff*T in little-endian; coefficient wires 23..26 hold m_eff. Decode zero if m_eff=15. Other packed input bits retained. Correct first-stage product for this specific midpoint model is 4mT+2m; rounding and addition of C3 are not emitted. Different from PR132's 6998-CCX weighted snapshot; not a like-for-like gate reduction.

## Full-domain arithmetic-only audits and search

PR132 original truncated bit-column product is not identical to truncated Booth recoding. On all legal x, worst error/tolerance original 0.9137239685, signed Booth 0.9018848488, ordinary rounded 0.8906356831; zero violations for all. Minimum absolute margins 54096592,62050667,69270543. PR139's 1234 CCX four-stage Booth figure is a cost estimate, not an emitted width-bounded reversible multiplier.

Selected repaired_k12 model: exact all-domain margin 127738159, worst ratio 0.8215557105764351, zero violations. Phase specification SHA 6bd733d6a3161b4e5fd33573fcf270eea50727ca6ae82db3ebca1dbf0b956851. Retained variable bit-pair bound 845 (48/211/266/320). 32 generic rotations in the proposed B35 output specification, no native phase consumer yet. This uses different coefficients, midpoint handling, and precision from PR132's 969-pair B34 model. Search screened ten degree/segment/precision configurations in approximately 3.4s after reference preparation; compensated rounding via Chebyshev coefficient exchange and integer interval repair produced selected model. Some aggressive sampled candidates failed full verification; broader compensated scan was interrupted by a time limit. No optimality claim.

## Research budget and open work

At 36Q, previous fixed proxy 60927.55/Q=1692.43 total, 32 rotations at historical average proxy cost ~231.76, so after 497 paid first macro ~963.7 expected paid remains for all other work. This is conditional planning only, not a score estimate verified for the new angles. Need a bounded-width non-recomputing C3 addition and remaining stages, terminal rotation consumer, inverse, then official verifier. PR140 reports a distinct two-stage 1034-paid/707-rotation phase diagnostic; not additive.

Lean finite identities for the 4-bit carry and packed tag are separate from the native serialized replay, which checks each independent measurement phase term. Companion archive includes complete Python, pinned source dependencies, NPZ coefficients, KMBs, receipts, and portable replay commands. Gidney temporary logical-AND/HMR and windowed arithmetic inform the design; no claim to reproduce an entire external algorithm. No official verifier, competitive score, or submission.
