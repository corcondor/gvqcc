# V59 — actual consumer of PR138's weighted intermediate (NOT SUBMISSION)

Native partial circuits, NOT complete invsqrt and NOT a score update. Based on PR138, with the joint coefficient loader from PR140. PR139 Booth counts are estimates; not a low-cost complete multiplier.

| variant | Q | expected paid | arbitrary rotations | ops |
|---|---:|---:|---:|---:|
| Booth corrected first product stream |30|409.5|0 (snapshots)|2338|
| Booth low 3-bit phase + cleanup |32|704|3|3805|
| Booth low 5-bit phase + cleanup |34|2222|5|5817|
| complete normalized two-stage phase, low column accumulator |35|8802|661|20719|
| coefficient value contraction |36|1054|676|7918|
| coefficient contraction + triple carry |36|1342|577|10357|
| coefficient contraction + triple carry |34|1389|577|10458|

All independently reread native circuits checked on 3,133,452 legal x, every independent HMR phase coefficient, input/work restoration and the specified intermediate output. The phase variants match the normalized V57 phase modulo 2^32, not full invsqrt; code SHA e4a7a79b75dbca5f375f48fb94ab52e3da0e987ca4b773844223d64b18041292. Q34 compressed SHA 8d5bfa0a4b5ea7cc253d560d2f51077332ea20c5d530ce0ab2d79d3f1d19e0d5. Booth Q30 SHA 0bb6b8cb8c6400f4e04c9c843d7616b6794883fe8b276f3defd8d69bb4ee8bc3. Different Booth rounding changes 2,792,640 outputs by up to 7 units vs retained bit products. Not a full canonical multiplier.

Booth digit d=a+b-2c, H=floor(C/2^s), u=C_(s-1): towards-zero truncation = dH+u(maj(a,b,c)-c). Adjacent digit cancellation gives ordinary retained products plus unit-weight corrections; native row sharing. This does not establish global optimality or an economical Booth adder.

Merge 742 terms into 90 integer vectors on 24 addresses, 676 signed bitplanes; 128 distinct coefficient masks. Complement/gcd/offset search did not improve rotation count. Forced complement variant 709 rotations/E1160 rejected. Partition identical coefficient masks and equal weights, 99 triples, use shared majority/parity and measured AND erasure. Residual first-factor sharing via exact minimum vertex covers of monomial graphs. All rotations generic. The low-column accumulator is expensive because carries and inverse consumer force recomputation; rejected.

For the pinned verifier, the best possible min_margin is bounded by tolerance of x=3133452, 621138291 integer units. At Q34/E1389, at most 59 generic rotations are affordable even before remaining stages; at Q36/E1342, at most 51. 577 is still noncompetitive. No official verification, no full oracle, no main or Kaggle mutation.

References: Gidney https://doi.org/10.22331/q-2018-06-18-74; AlphaTensor Quantum https://doi.org/10.1038/s42256-025-01001-1; low-qubit squaring https://doi.org/10.1007/s11227-026-08255-5; Halpenny et al. https://arxiv.org/abs/2611.26605 (Fourier/in-place approach not directly available in native basis). OpenAI Fourier/matrix exponent finite sharing ideas, not a port of asymptotic algorithms. Local Lean identities only; no full formal KMB proof. Archive GVQCC_V59_ActualConsumer_NOT_SUBMISSION.zip SHA256 0009713e7cb1b23e5dad0f3955950a2da3113f5531b6a37629f31763e0d9bfff contains full scripts, source dependencies, all native artifacts and receipts; supplied in research conversation.
