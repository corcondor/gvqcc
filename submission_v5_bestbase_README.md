# Preferred submission: public DQI 821 hash + inverse e46 + score2 chemistry

This separate artifact preserves the exact public DQI file with SHA256 prefix `821bf8d157c0`, inverse `e46d90c3`, and the newly verified, matching score2 chemistry family. The prefix `821` identifies a file hash; it is not a qubit count. The earlier e986 fallback is retained unchanged.

## Ready ZIP

- Path: `/workspace/scratch/7f542e06b7cf/submission_v5_bestbase/submission.zip`
- SHA256: `84d373c032b1e5d852a358db29fd830cc65f4889235c1e8ac03316dad7350032`
- Size: 49,229,452 bytes
- Contents: exactly 18 files, all expected uncompressed hashes and archive CRCs checked
- Receipt: `submission_v5_bestbase_local_receipt.json`

## Kaggle reconstruction

Worker: `submission_v5_bestbase_worker.py`, 578,707 bytes, SHA256 `733e2fd16c66af249a4b774546e12900d9deac31fa7c87b491ec94d3e4548ca2`.

Attach these inputs to a fresh CPU notebook:

1. The competition data, with official verifier and KickMix engine.
2. Output of `geocpuresearch/gvqcc-verified-480ccx-gauge128`, **version 1**, script version ID `369627280`, for the exact baseline coefficient NPZ and inverse circuit.
3. Dataset `manwithacat/vqcc-apache-public-circuits`, containing `circuits/dqi/821bf8d157c0.kmb`.

Run the worker. It requires the exact known DQI hash; it does not accept arbitrary alternate DQI bytes. It can also recover those exact DQI bytes from an attached original full portfolio if present. Source discovery was exercised locally using the actual prior ZIP and public DQI input.

The worker reconstructs the score2 NPZ and 15 circuits exactly, verifies all 91,500 angle words against the circuits, and runs the official 78,080-shot chemistry validation. It writes `/kaggle/working/submission.zip` and receipts. It neither calls a Kaggle submission API nor requires network access or credentials.

## Validation and score

The chemistry family passed a fresh official verification: `PASS`, 78,080 shots, cost 294988052.12610483, lambda effective 46.906472675810164, 14,728 Toffolis and 427 qubits. The complete verification receipt is `results/2026-11-15/submission_v5_dfthcsos_verification.json`.

The public DQI bytes are SHA256 `821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3`, size 455,584,321. Inverse bytes are SHA256 `e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6`. They are preserved without rewriting. No additional full DQI/inverse quantum verification was run during packaging.

This matches the component hash prefixes in the historical `4033/821/e46` submission description, but the entire historical 27.30683 ZIP has not been recovered and compared. Do not claim that portfolio's exact identity or a higher public score before Kaggle returns this candidate's result.
