# V54 — strict physical 22Q, prefix-direction tensor transport and fiber embedding

Research only / NOT SUBMISSION. PR119 is the 22Q exact-plan baseline; PR121 and PR122 are distinct low-rotation lineages. No 37Q working register in any V54 emitted full circuit. No main merge or Kaggle mutation, no official verifier/score. Do not confuse analytic feasibility with competition feasibility.

## Native independent replay results

| variant | Q | CCX | generic rotations | native ops |
| --- | ---: | ---: | ---: | ---: |
| PR119 same plan |22|55606|15287|115245|
| shared direction |22|22353|15287|80031|
| tensor7 (same PR119 phase)|22|8168|15709|62714|
| minimax7 (new analytic phase)|22|8152|12921|53868|
| minimax15 (new analytic phase)|22|9976|12713|54950|
| minimax30 (new analytic phase)|22|13064|12526|58479|

Full 2^22 serialized gate/control replay, input restoration, exact modular reconstruction of each target plan; exact squared analytic tolerance all 3133452 legal rows. Minimax7 worst ratio 0.7969746440649033, x1302776; independent official-style integer proxy margin 131008742 and zero violations. Not source-phase equality for minimax variants. SHA256 shared 48860e8feb8fe7c99cb6bf6a6bc55147e6ea5ac89f231c89628167c70f11f085; tensor7 6c7261fe542c5e76c962e7e0fab83fb2a1b5aeb16d621155af6d381602394877; minimax7 1421229430d4197d7a5d0366867a62f3bfce691d2eaa548ade541ef4fd8d31a9. No HMR.

Implementation: exact sibling Walsh coefficient lifting (even sums only), shared suffix direction with s·v=1, rank-one transition (v XOR w) I_p XOR w(I_p XOR I_q); I_p XOR I_q is an affine 2-point line and needs d-1 prefix controls. Compare four direction schedules and 20 route warm starts (2 fixed +18 greedy), 2-opt. Finite sparse Walsh feasibility with Douglas-Rachford projection and exact integer rounded acceptance, 13453 -> 11047 spectral terms. Negative trials not lower bounds. All exact phase reconstruction independently checks output bytes. Objective explored CCX/rotations Pareto; not official optimum.

## Low-rotation existence versus cost

PR92 fixed-history exact phase controls (39 nonzero terms including grid/sign; existing total-phase history independence from PR92). On D={1,...,3133452}, a single coordinate of a 22-bit permutation may have weight only between N-2^21 and 2^21. 27 roots qualify (25 generic). Construct explicit joint encodings with 14,11,1,1 outputs respectively; max fibers 254/256,1912/2048,1658373/2097152,1917655/2097152. All legal rows injective and all selected bits match. 41 exact packing trials; not a global partition optimum. Fiber rank fills remaining bits. An injection extends to an even permutation by completing illegal rows and adjusting parity there. Shende et al. (quant-ph/0207001) imply an ancilla-free NCT realization; no efficient permutation circuit supplied. 

Other 12 terms include constant and 11 nonconstant small-support controls (after complements). All support x<2^20; x XOR (3*2^20) is illegal. Shared marker and legal-to-illegal swap, exact weighted XOR-prefix cover and Held-Karp tour: actual 22Q suboracle 98645 CCX, 123539 ops,14 rotations/11 generic; independent computation route 176640 CCX. SHA f3525cb17c303803c18b784d25d57ab1f75e98f9d1dd9e2ae1c1e7b8cf1c897a. All cube control masks, exact PR92 partial phase on legal rows, restoration PASS. Two-high-bit half-angle echo alternative 115462 CCX/143537 ops/26 rotations, exact same partial phase PASS, rejected. 146 dirty comparator macros independently verified across all cube states. Combining the abstract even-permutation realizations and measured native rare suboracle proves a finite 22Q, at most 36 generic rotations (41 total) existence bound for original phase; NOT a full low-rotation emitted KMB or cost bound. Haar alternative 708 bitplanes and 727 rotation estimate, 32998178 CCX macro estimate; exact analytic squared tolerance zero violations, not emitted, rejected. No low-cost original phase oracle solved.

## Cost/roadmap
Pinned PR121-style proxy E+rotation equiv: best37Q total product 60927.55; at Q22 target <2769.43409. If 33 generic rotations have proxy 239.0039, E must be <2530.4302. V54 minimax7 proxy R~105832, far from target. Thus shrinking rotations and realizing cheap reversible permutation/low-complexity shared Boolean evaluation remain essential. Prior V53 33/32 control variants and negative Farkas results remain relevant. No 37Q candidate is proposed as answer to the 22Q objective.

## Literature
Amy/Azimzadeh/Mosca parity-network synthesis (arXiv:1712.01859), Khattar/Gidney conditionally clean ancillae (arXiv:2407.17966), Shende et al reversible even permutations (arXiv:quant-ph/0207001), OpenAI 2026-11-24 finite Fourier and matrix exponent 9/4 manuscripts. Concrete transfer: parity sharing, dirty control toggles and finite sibling/rank-one contraction; even permutation theorem only for existence. Not a port of OpenAI's asymptotic algorithms or a CCX upper bound from those theorems. Provided X post could not be read (HTTP 403), no attribution of its specific content. Lean proves local Boolean/integer/projection laws, not all native bytes or official verifier. Native replay, source and reproduction archive in conversation. 
