# Virtual boundary phase potential (2026-11-24; research only)
Parent PR54 head d2699ed4affb6b2997028e30fc02000b13c3c0e1. PR51 phase syndrome, PR44 phase transport, PR43 rankhub, PR53 vector rank and PR55 moving tensor reports reviewed. This is an analytical extension, NOT a claim of unprecedented literature or completed full-history novelty audit. No ANGLE exploration: historical source archive blocker persists.

## Exact phase and restricted negative audit
PR54 source [26344,26426) virtual phase P=(ab XOR a XOR c)*(1 XOR x XOR y), a=q27,b=q28,c=q25,x=q2,y=q18. Existing 7 X/CX/Z/CZ/CCZ instructions (one CCZ; separate classical measurement instruction excluded) verified over all 32 assignments. Exhaustive closed X/CX frame paths with exactly one CCZ and total <=6 gates: counts by affine steps 0..5 = 1,0,25,0,1645,800; distinct CCZ-mask probes across paths = 60770. All fail even allowing global sign. Applies ONLY to these five wires, no ancillas, HMR, guards or additional wires. Not a general lower bound. Do not repeat the same restricted audit.

## Boundary potential
If a data operation ALREADY changes t to t XOR f, with affine h invariant, then f*h = (t*h) XOR ((t XOR f)*h). Across arbitrary increments, parity of f_i*h telescopes to t_start*h XOR t_end*h. Both endpoint phases can be emitted using Clifford gates. This is joint data/phase synthesis: solve for NEW free Z/CZ phase potentials at legal cuts, not merely delete existing phase-syndrome columns or move an existing phase. Prior V8 nonlinear phase transport overlaps conceptually; full native-source comparison mandatory before optimization. General equation P = XOR_i Phi_i(u_i,m_i), Phi_i degree <=2 in physical coordinates for fixed classical history. Preserve full data, guard, HMR and real-angle semantics. Affine decoder and injectivity constraints still apply.

## Actual executed prototype (synthetic carrier premise)
For the PR54 polynomial, assume an existing 3-instruction data update on a sixth live wire t: CCX(a,b,t); CX(a,t); CX(c,t). Direct phase + data = 10 ops / 2 paid; endpoint phase + same data = 9 ops / 1 paid. Three cyclic increments (a,b,c),(b,c,a),(c,a,b): 30 ops / 6 paid -> 15 ops / 3 paid. All 64 assignments, exact data and sign match, 6 wires. This is NOT an actual PR54 KMB splice: carrier update is hypothetical. Exact endpoint Z/CZ dictionary rank24 contains P, whereas identity-transition dictionary rank21 does not contain P. Prototype and exact restricted audit in user archive GVQCC_virtual_boundary_20261124.zip SHA256 6797a136698f6f18a94266b07d6aa4c7341b7be7b86c51c22e0ecb6e959af726. Run python audit_phase.py and python potential.py. Lean file includes local Boolean and arbitrary-list telescoping source; Lean not yet run. No full native KMB, no official KickMix, no score gain, no main changes or submission.

## Fixed score gate
PR54 integrated cost 41812 instructions / 1846 static / 1676.3125 expected / 37Q; width-first 42767 / 1878 / 1697.3125 / 37Q. PR54 comment reports 549 q36-touching instructions in wide, 1286 in cost. Conditional score model PR51: Q36 must reach E<1452.05390236 to exceed 33.1703164053 with other costs/overhead fixed. Cost branch still requires >224.25859764 expected paid savings, after complete 36Q. No arithmetic addition of PR55 donors.

## References and relationship
- Amy, Towards Large-scale Functional Verification of Universal Quantum Circuits, https://www.mathstat.dal.ca/~mamy/Papers/pathsum.pdf : phase/data path semantics.
- Yang/Yuan, MBUndo, https://arxiv.org/abs/2611.02345 : sound measurement-based ancilla removal.
- Ruiz et al., Quantum circuit optimization with AlphaTensor, https://doi.org/10.1038/s42256-025-01001-1 : shared phase gadget synthesis.
- Modular Synthesis of Efficient Quantum Uncomputation, https://doi.org/10.1145/3689785 : structured uncomputation.
- PR44/51/54/55 in this repo are comparators; references are not evidence of native improvements.
