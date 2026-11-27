# Exact 316k native arithmetic boundary — unresolved, NOT SUBMISSION

Parent SHA256 2c8ea3ad0cbf316b6392fb7ffd2fb04d3059633d8d66281228abe13b496c4e60, 900Q, 62,086,097 operations, 318,584 static paid. Different from the 69,782,188-operation donor. No modified circuit or score claim.

Using 64 random w35 syndromes as calibration, match the 4095 nonzero GF(2)-linear bit forms of each existing GF(4096) reference coefficient to physical bit signatures. At original op boundaries 32,727,000 and 38,919,000, 35x12 independent forms recover B. At 47,121,000, 35x12 independent forms recover A. These are empirical maps, not universal symbolic equivalence certificates.

On a disjoint 64-case mixed-weight panel using these maps, with zero external mask, both zero HMR outcomes and randomized outcomes (seed 431) give the identical 10 mismatches of A*D=N*B against the exact sparse rational pair. Failed indices and weights:
6:6,8:8,10:10,12:12,16:16,41:6,43:8,45:10,47:12,51:16.
Nine miss all true roots; the first w6 misses five of six. No choice of the implicit leading coefficient alone recovers all true roots on any of these ten. B is unchanged across both recovered cuts for all 64 cases.

Explicit witness (w6), nonzero field element -> magnitude, modulus 0x1053:
{3383:4039,2361:1651,2832:554,3618:1697,1214:356,3819:1264}.
w10: {316:4003,863:443,2583:1222,3272:1088,2651:1646,938:1102,2518:3259,1941:708,429:1201,3764:2649}.
The moments are S_j=sum e_x*x^j, j=1..70. Reference D=prod(z+x); N=sum e_x*x*U(x)*D/(z+x), where U=prod (z^2+z+k)^2 over k=3169,3257,3134,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054.

`verify_boundaries.py` checks the physical maps from `highmap.tsv`, snapshots, and the known error panel. These data, KMB capture sources, and prior direct_codec.py are in the companion archive GVQCC_316K_Native_Root_Diagnosis.zip. This is a regression to preserve while repairing the original arithmetic, not a separate optimization objective.

Restoration and phase defects remain. The failing locator is already present before the B scan, so terminal phase-only fixes do not suffice. The first faulty physical operation and a fully repaired KMB are not established.

## Inverse-head and jet refinement (2026-11-28)
The earlier polynomial comparison is insufficient to locate the faulty arithmetic. The native first 16 head coordinate fingerprints recover the inverse-leading recurrence D+hN=gQ, next pair (Q,N), with the actual node order in corrected_jet_model.py. For a numerator divisible by g, retain the separate no-swap branch (N/g,D). Do not conflate a vanishing head with termination.

Use the historical zero-safe involution J(u,v)=(inv0(u),v*safeInv(u)^2), safeInv(0)=1. A terminal jet (0,0) stays zero; a nonzero derivative in the zero fiber must not be erased. The reverse post-transport shares one reciprocal of q. This corrects the reference recurrence and prevents an invalid simplification in subsequent repair/optimization.

Original-tape prefix KickMix 1.0.0, 64 mixed inputs, seeds 17 and 431: at 22,609,000, the same two w8 lanes disagree in all 13 mapped jet groups. At 25,378,500, the same six lanes w6/8/14 disagree, first at heads 10/10/16 respectively. These are measured prefix comparisons using calibrated field forms, not a certified universal physical wire mapping. An independent bit-sliced replay first observes a disagreement after op 22,605,433 (zero-based). Do not identify that CNOT as the faulty gate. The derivative mismatch and later low-weight restoration failures still need an exact forward/reverse splice.

The reused historical safe jet, pro jet, and retained inverse-norm alternatives all pass two 1024-shot forward value/ancilla tests and two 1024-shot roundtrip value/ancilla/phase tests (including 256 u=0 inputs per seed). The retained-norm variant reduces executed paid gates but raises static paid and width, and is not selected as a full-circuit improvement. The actual 316k gate list has NOT been replaced and no CCX/Toffoli or competition score reduction is claimed. Native measurements and reference checks are in jet_receipt.json; reproducible local scripts, native coordinate mapping and input panels accompany the research archive. Lean field proof is ZeroSafeJet.lean, checked by the existing cutoff18 workflow. No phase-only compensation accepted.
