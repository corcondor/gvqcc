# Adaptive Hermite pivots — research only, NOT SUBMISSION

Parent independently replayed: 2c8ea3ad0cbf316b6392fb7ffd2fb04d3059633d8d66281228abe13b496c4e60, 900Q, 62,086,097 instructions, 318,584 static paid. PR #227 parent 4b572141… is a different binary. Never transfer a certificate between them.

## Independent checks of PR #227
149 and 172 paid-gate predicates: 1,810 shots each, no errors. Norm vs conjugate predicate: 37,769 exact comparisons. 32 legal w16 distributions constructed by confluent linear constraints force first poles at heads 3, 5, 7 respectively for padding scales 1, 2, 3, despite the shared selector passing 64/64 shots. On the original 2c8 parent, each scale has 64/64 value failures; phase errors 30,33,33. Scale 4 has zero errors in the same 64 shots, not an all-input certificate.

## Mathematical repair
Use U of degree 70 (17 doubled irreducible quadratics and one extra singleton), 35 slots. Maintain coprime N,D and deg N < r, deg D <= r. Each distinct remaining quadratic has 2 distinct conjugate roots and at most 2 slots. If nonzero N vanishes at every available node, it has at least r roots, contradiction. Select a nonzero numerator, h = (D mod g)/(N mod g), Q=(D+hN)/g. New pair (Q,N); degree bound drops one and coprimality remains. At other roots use homogeneous transport (d+h*n,g*n) and differentiated transport, without a division by g; at the repeated selected root use g'=1. If N=0, D is a unit. Reverse actual selected steps and normalize. Initial transformation GF4096 rank 70 (GF2 rank 840). Independent mathematical reference tested 1364 cases, including 216 forced poles and 32 inputs requiring the singleton; exact restoration and sign check all passed. No physical width bound for the homogeneous jets or complete reversible pivot history is established.

Hankel: H=V18 diag(e_i*x_i) V35^T (moments indexed S1 onward). Rank min(w,18) for legal w<=35. Full rank, not leading-minor shortcut. Replayed historical rank reference, 432 legal +553 saved +32 matched prefix pairs, not a synthesized rank predicate.

## Native initial pivot selector on raw S
840 S, 5 XOR target bits, 40 clean ancillary qubits. 432x840 Boolean linear certificate. Priority telescoping: XOR i^(i+1) under prefix zero-product p_i. Sentinel 18. Two independent measurement seeds, 304 cases per seed, including 32 singleton-required and 4 zero syndromes, 128 arbitrary S. All data, target, ancilla and phase errors zero.

| variant | Q | static paid | average paid | instructions | shots |
|---|---:|---:|---:|---:|---:|
| direct erase |885|845|845|151517|608|
| HMR central |885|827|628.7105263157895|151571|608|

KMB SHA256 direct 04cc1343d620afc356697a834f0afead3d4084a2360e48f05d78336843407084; HMR 2cdbf0f51f41fd49109509f10f2f236da4eb8b198b62f2879a6aed8d1b2c7cee.

This is a local selection circuit on original input, not a repaired decoder. A complete physical 35-step dynamic ordering, reversible history/label management, reverse restoration, HMR phase debt and total cost remain open. The new U changes the initial map; no old-tape splice is implied. No full circuit cost or score claimed. Complete experimental source, fixtures, local KMBs and receipts are in the separately delivered research ZIP.
