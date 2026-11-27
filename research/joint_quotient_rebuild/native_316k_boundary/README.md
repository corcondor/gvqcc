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