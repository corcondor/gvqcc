# Native locator seam: Frobenius projector and dirty prefix echo

Parent: #295 head 3a257b43818249a7dffa37b776408f01a70dc9ad.
Native comparison source: #290 KMB SHA-256 2545a84896ba44152eab0db6856a056d23f60869c60fac8e7d1a8788c51e88dd; locator seam 36287888.

For q=4096 and P supported on physical linear factors and trace-one irreducible quadratics g=X²+X+k with multiplicity at most two,
E=(1+X+X^q)^2 mod P is a CRT idempotent: 1 on physical factors and 0 on the ghost factors, including their squares. Therefore the physical part of a trace pairing is Tr(X^(j+1)VE). This assumes P and V represent the correct data. No claim for arbitrary defective P. Constructing E has a modular squaring cost; it is not a free circuit.

For a known g, let a be the negated bits of P mod g and b the negated bits of P' mod g. The dirty echo evaluates AND(a) XOR AND(a+b), i.e. exactly-one multiplicity under the multiplicity bound, and adds its product with a 24-bit payload to arbitrary targets. All borrowed bits restore. The proof file formalizes local identities, not the full CRT or circuit semantics.

Local executed results:
- 528 captured #290 locator states, 17 known quadratic factors, 8976 native-coordinate gate replays; zero predicate, payload, and reverse mismatches. Arbitrary payload probe, not identified native V. 900 physical Q, no additional Q in probe; 40997–41147 affine gates per frame direction.
- Fused local 24-bit kernel: reference 592 CCX, new 234 CCX +4 CX; scalar indicator 184 CCX +2 CX. 8192 forced/random states and 1280 exhaustive smaller states, all exact.
- Reference Frobenius arithmetic on captured P, synthetic V: 507 valid charts, 35490 moments all match independent physical-root sum; 21 unsupported charts fail idempotence and moment comparison. Not a full-circuit error-rate estimate.
- Full DQI return splice, exact amplitude ABI, earlier defective locator, full expected paid count and standard-size verifier remain open. No score improvement or new submission claimed. #292 candidate unchanged.

Run python3 check_prefix.py from this directory. Full capture-dependent source, probe and receipts are supplied in the accompanying local research archive. Lean CI is separate; do not count statements as verified until strict check succeeds.
