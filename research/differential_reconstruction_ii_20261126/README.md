# Differential reconstruction II — research only

Follow-up to PR #166. No new competitive score, no official verification, no Kaggle submission, no change to main. No new 37Q design.

## Native results
- 25Q: 5007 -> 4964 -> 4963 CCX, 7777 generic rotations unchanged, 61260 -> 61303 instructions, formula cost 1695645.4891464112 -> 1694545.4891464112.
- 36Q: 1358 -> 1355 CCX, 7850 generic rotations unchanged, 50906 -> 50908 instructions, formula cost 2332126.5622262387 -> 2332018.5622262387.
- Both verified over the entire 2^22 input cube, including input restoration, equal rotation controls and angles and independent HMR phase coefficients (2750 and 1259). The previous legal-domain tolerance transfers by equality of the phase function. Both remain noncompetitive versus the existing low-rotation reference.
- DQI: all 68,799,061 instructions inspected, 318,950 static three-wire paid instructions unchanged. 550,224 cross-scope queries yielded no paid saving. Conservative width audit: 668 potentially full-width episodes, 350 rank-deficient at entry and 318 full-rank in the overapproximation. Not a lower bound. First overfull interval 20135348..20135412 has an exact 14-to-13-wire **data-map** chart, verified on all 8192 independent local inputs. Phase/HMR handling and global 899Q construction are unproved.
- DFTHC-SOS: all 15 banks, both directions on 1219 addresses, 150,207 delayed affine-frame cut tests, no new paid reduction (3357 CCX/pass). Exact continuous Jacobi-pair search reduced the W/H2_I gauge L2 surrogate by only 2.03e-10; not adopted or counted as score gain.

## Theory
For Boolean t'=t XOR p, if the post-update residual t' is affine in other surviving wires, XOR it into t, HMR the resulting product p, cancel the independent measured phase m*p, and restore the residual. For a CCX with an unread target until HMR, transport its product to the HMR cut. A representation by degree <=2 Boolean functions of other live wires permits Z/CZ correction and removes that CCX. The general difference law is Delta(ab)=a Delta(b)+b Delta(a)+Delta(a)Delta(b) over GF(2). Delayed reconstruction is possible in phase-free segments when both care-state matrices, augmented by a constant row, have equal row spans: Gaussian row operations give invertible affine recoding.

## Artifacts
Full scripts, native 25Q/36Q KMBs and receipts: GVQCC_Differential_Reconstruction_II_NOT_SUBMISSION.zip, SHA256 90fbe00e6ece365c4e83eb8c8d0c0b3ce91ecc5d5d595c2463c495bc2710ed8c (delivered separately). DQI and chemistry unchanged KMBs referenced from parent #166 archive. The small Lean source below is uncompiled; 36 local Boolean assignments passed Python enumeration. Official runtime packaged for CPython 3.12, available environment 3.13; full official verifier not run.

References: PR #166 #165 #164 #157 #155 #19; Amy & Lunderville DOI 10.1145/3704873; Meuli et al. DOI 10.1038/s41534-021-00514-y; Gidney DOI 10.22331/q-2018-06-18-74; Khattar & Gidney DOI 10.22331/q-2025-05-21-1752. No full algorithm port claimed.
