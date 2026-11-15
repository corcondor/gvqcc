# Sources and credits

- **invsqrt** — the file 1ba197b0, byte for byte, as shipped in heliosli's notebook https://www.kaggle.com/code/heliosli/the-dataset-is-public-now-enjoy (version 55);
  its authors and the invsqrt lineage are credited there.

- **dqi** — the 889-qubit file 821bf8d1, byte for byte, as shipped in areebbb's (Areeb Ali) notebook https://www.kaggle.com/code/areebbb/qai-fewer-toffolis-same-qubits-lb-27-31224
  (version 8; Apache-2.0): Syed Asad Ali's (syed3000) v12 DQI decoder from https://www.kaggle.com/code/syed3000/vqcc-own-circuit-portfolio-notebook (Apache-2.0) rebuilt at
  extractor cutoff 18 (Ertuğrul Özer's (ozertuu) cutoff idea, https://www.kaggle.com/code/ozertuu/quantum-ai-27-083-vqcc-dqi-cutoff-17) with areebbb's 241 retained
  products, as credited there; the earlier DQI lineage is credited in those notebooks.

- **dfthcsos** — arizalfirdaus123's (8, 143, 44) DF-THC table, its angle words and its 4,030-Toffoli angle
  circuits k = 0-14, byte for byte, from their notebook https://www.kaggle.com/code/arizalfirdaus123/vqcc-analytic-gradient-df-thc-mbuc-optimization (version 9). The table weights
  (W, H2_I) in this version are our update of boristown's weights from their notebook
  https://www.kaggle.com/code/boristown/qcc-gap-3-residue-repair-and-c43-native-compiler (version 6; the lineage of their weights is credited there), made with prvsiyan's refit code
  (code/refit_grg.py and code/chemlib.py in their dataset https://www.kaggle.com/datasets/prvsiyan/vqcc-verified-best-of-circuits-1106a, Apache-2.0).
  The chemistry lineage is credited in their notebook and the notebooks it names.

- **Further weight-refinement code (this reserve snapshot)** — boristown's published `refit_dfthc_v2.py`, from https://www.kaggle.com/code/boristown/qcc-gap-3-residue-repair-and-c43-native-compiler. The earlier chemistry and optimizer lineage is credited above and in that notebook.
  Lera's NOTICE (Apache-2.0), as carried in her dataset:

  > DF-THC 11.2x: (8, 143, 44) table and loaders
  > Copyright 2026 marculera (Kaggle)
  > 
  > Licensed under the Apache License, Version 2.0 (see LICENSE). The weights and words in submission.npz were trained and
  > rounded by us from the competition's FeMoCo Hamiltonian, with no public weights or tables. The arrays H1_I and
  > Hsym_lower are the hosts' fixed shifts, as published in the starter kit
  > (sohier/verifiable-circuit-compilation-starter-kit). No file here is copied from another dataset.
  > 
  > The build rests on public work, credited below as ideas; no code or data of the people named ships here. Each source
  > keeps its own terms (some Apache-2.0, some "other"). The public code our pipeline adapts is Apache-2.0:
  > ahmedberatozer's group-compression notebook code, and the kernel-relation search in qwertykeypadapple's src/
  > (Apache-2.0 per its NOTICE.md).
  > 
  > The table
  > - Seed: the clustered (8, 143, 45) seed of marculera/dfthc-compact-pipeline, built from the Hamiltonian; its NOTICE
  >   lists the public work it adapts. Everything after the seed is new here.
  > - Exact gauge refinement of the offsets W: adapted from chemistry_refine.py of ahmedberatozer's group-compression
  >   notebook (Apache-2.0), which credits kozykappa's column rotations and anazemcev's effective-norm method.
  > - One-body rows refreshed from the decoded two-body part: the role of mrmeows' refresh_one_body8.py (own code).
  > - Staged progressive rounding: ahmedberatozer (vqcc-v8-components); L-BFGS stages: michaelrustad.
  > - Sign mixing D(w) as the quantity that sets the one-norm: ahmedberatozer (group compression).
  > - Rounding: syed3000's public notes on his own (8, 143, 44) table (vqcc-own-circuit-portfolio); our implementation is
  >   independent.
  > - Joint (w, W) refit at fixed words: phucthaiv02 (qcc-verified-portfolio-df-thc-retraining-study); refit up to the
  >   gates: heliosli, busyaprime; a constrained refit at fixed words developed independently the same week and the
  >   alternating gauge rotations of his refit tool: James Barlow (manwithacat, Hedge Wizardry HW-03); zero-weight active
  >   sets: maoxin123.
  > 
  > The words
  > - Coded low bits, one affine pattern per block of 16 addresses, on bit 0 of every word and in some circuits on bit 1
  >   too: somejoint (qcc-our-chemistry-b143-c60-xor2, Apache-2.0).
  > - Codes on XOR directions of the five words of a batch, at bits 1 and 2: ours.
  > 
  > The loaders
  > - Signed Givens gauge (a word's top bit equals the bit below): kozykappa, Kozykorpesh and Sumit Chongder.
  > - Exact lookup emitter design: mrmeows (qcc-1375-open-circuits). ANF loading of the batch deltas: the banked QROM of
  >   kozykappa, Kozykorpesh and Sumit Chongder (via ahmedberatozer's banked_lab.py). Borrowed top bit: heliosli. Padding
  >   rows as don't-cares: James Barlow (manwithacat, HW-18/19). Five words per circuit: heliosli, lightningv08.
  > - pi-gauge helper encoding (a word's top bit holds a low address monomial): Atakan Aldemir.
  > - Five-block low-monomial plans: syed3000, read from his published circuits; his notes describe exact matroid-parity
  >   pair selection. The parity count here uses Lovasz's rank formula (L. Lovasz, Matroid matching and some applications,
  >   J. Combin. Theory Ser. B 28, 1980).
  > - From gengsr's published loaders (vqcc-25-2268-portfolio, Apache-2.0), read from the circuits: the
  >   four exact word forms (theta, theta + pi, -theta, pi - theta), the low-block partition used here, the product
  >   pattern that lets a loader with five dirty words fit in 128 qubits, and the class count that showed our plans had
  >   room. Our layout program, cache scheduling and planner are our own code.
  > - Kernel-relation search in an earlier loader family: qwertykeypadapple.
  > 
  > The hosts: the official verifier, kickmix and the starter kit.

- **Organizers** — task definitions, verifiers and kickmix (Google Quantum AI / Qualtran, competition data).
