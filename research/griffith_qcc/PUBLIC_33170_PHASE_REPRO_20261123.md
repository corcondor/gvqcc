# Public 33.17023: exact inverse-sqrt three-T reproduction, no new score

Source: https://www.kaggle.com/code/mizeroluckygall/quantum-circuits-33-170-3-357-toffoli-loaders

**Status**: Public Kaggle notebook score 33.17023. Our old V8 comparison basis is 33.13521306472748. **No independent leaderboard improvement, no native KickMix verifier run.**

## Methods actually executed
- Re-created the documented public 3-T -> 2-Clifford-S inverse-sqrt patch from the 37-qubit old KMB, without altering 17 remaining public V8 files.
- Original SHA256 `d2148a7cd7a4d0a004eca1e7b18f9fd1282df4ed3be4a9aa970842f9119fa307`.
- New SHA256 `bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b`, byte-for-byte equal to published public edit.
- Independent C++ bit-slice phase-signature replay: every `x=1..3,133,452` with HMR measurement modes all-zero, all-one, and seeded pseudo-random; modular phase-difference mismatches `0, 0, 0`. This is *not* an exhaustive proof over all HMR transcripts.
- Post-edit 10 remaining 1/8-turn phase gates screened on 131,072 inputs/seeded HMR: zero identical bit-phase signatures across different gadgets; the only exact GF(2) triple-linear relations on this sample are (32661,32662,32664), (34340,34341,34343), (35288,35289,35291). Their CCX dirty-target interactions are active, so naive local gate deletion is incorrect.
- Conservative invsqrt CCX pair scan: 1,470 CCX, 547 same-target/one-control-shared pairs within 120 op window; zero pairs with all intervening operations disjoint from the four relevant wires.

## Price implications and missing piece
- Old invsqrt cost 60,955.32670759028 -> 60,927.57670759028 (37Q × 3/4T equivalent), only a price calculation.
- Keeping 17 V8 files untouched would predict 33.14024287579768, not an official score.
- The public 33.170 implementation also has 15 chemistry loaders reducing 3,375 -> 3,357 CCX/pass, 13,250 -> 13,214 total chemistry CCX. **Those newer loader KMBs have not been retrieved or generated in our local environment**; the original Kaggle notebook source was not pulled with authenticated Kaggle CLI.
- Reproduction ZIP SHA256 `f63a5e590ead246cce82295ed28d3cace630d95108ae46adaf9a1c1624a4ed49`: `GVQCC_Public33170_ExactPhase_SourceStudy_20261123.zip`, attached in the ongoing conversation; includes the 18-file-independent invsqrt phase tester, CCX and T phase scanners, outputs, both public KMBs, notes, and SHA ledger.
- No official submission or success claim.

This phase edit is a **public varianceofx technique**, not an original optimization. Credit the Apache-2.0 Kaggle source and original contributors. Main branch untouched.
