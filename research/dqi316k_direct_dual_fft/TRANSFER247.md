# Exact #247 transplant, not submission

Base #247 exact 8b9d09f8... was rebuilt in Vercel session sbx_xO02qDDffxwowJ4AJA3h2cCHVLAE. Copy #256 dual-mask source at 80b614973a956e80fd32846cd54c6e61010a4abf and run against the pinned #247 full KMB, not the historical #239 donor. All source paths retained.

```sh
cd research/dqi316k_direct_dual_fft
c++ -O3 -std=c++17 dual_fft_repair.cpp -o dual_fft_repair
./dual_fft_repair /path/to/8b9d09f8.kmb dual247.kmb
python verify_dual.py /path/to/8b9d09f8.kmb dual247.kmb
```

The verified full output is 900Q, 318333 static paid, 69534364 ops, SHA256 81081a88c27b708322f0724a09197814a18646a4a9969984ab9cf76a6e6cd7fa. 2480 matched native shots per circuit: zero and dual-span masks 140 combined failures -> 0, ordinary dense forced 70/144 still fail, distribution 2048/2048 clean on both and 316126.84765625 mean paid unchanged. **Not an acceptable <316000 candidate.** No claim of a new official score or whole-domain repair.

Exact parent full-tape searches for classical-dependent control transport, affine quadratic pair/plane fusion and cubic plane phase folding found no paid savings. The latter three reproduce the parent hash. Scope-specific native phase leaves already use 10 CCX + 1 CCZ; swapping in the expensive generic rational scan is not a budget improvement. See receipt247.json for log command IDs. Ephemeral sandbox expired after replay; raw JSON and exploratory negative optimizer sources could not be exported. No expensive alternative adopted.

The new Lean statements formalize arbitrary dual-mask translations, common-factor cancellation at padded roots, and shared phase planes. Only dual-mask fast-path physically transferred here. The full-domain #245/#246/#248 decoder connection and #251 FFT seam remain incomplete; no claim that the algebraic lemmas prove the complete tape. Strict CI must pass before claiming the new statements formally verified.
