# GVQCC conditional phase and nonlocal structure audit — 2026-11-23

## Verdict
**No new official verified aggregate score. Do not adopt the previous 37Q invsqrt 9T→4S candidate.** Current comparison baselines: archived 33.13521306472748; published 33.17023. No candidate meets the requirement of three independent native KickMix-verified improvements.

## Critical counterexample: previous phase proof dropped classical conditions
- Source original 37Q invsqrt KMB SHA256: `d2148a7cd7a4d0a004eca1e7b18f9fd1282df4ed3be4a9aa970842f9119fa307`.
- Three removed T gates at source operations 32662, 32663, 32665 are under `PUSH_CONDITION b743`. Another three at 34341, 34342, 34344 are also under b743.
- Previously inserted S gates after operations 8145 (q35) and 8344 (q36) are **unconditional**, prior to b743's computation.
- Prior exhaustive symbolic proof ignored classical guard masks when adding diagonal phase contributions. Its assertion of *all measurement branches* was unsupported.
- New independent bit-sliced branch-aware executor tracks `BIT_STORE0`, `BIT_INVERT[_IF]`, `PUSH_CONDITION`, `POP_CONDITION`, conditional quantum state updates and HMR outputs. Exact differential phase in units π/4 across all `x=0..3,133,452`:
  - All HMR outcome bits forced **zero**: 1,300,770 inputs fail (bins mod8: [1832683,0,953621,0,347149,0,0,0]).
  - All HMR outcome bits forced **one**: 749,964 inputs fail (bins: [2383489,0,749964,0,0,0,0,0]).
  - x=0 is a witness on both fixed-output branches.
- Published unconditional-only 3T→2S control passes **both** complete-input fixed-HMR patterns with zero differential phase mismatches; that is a negative-control/repaired-KMB experiment, **not** a novel improvement and **not** an exhaustive proof over all HMR outcomes.
- Rebuilt KMB 37Q, 1470 CCX, 55 Z_POW instructions: SHA256 `bb676b95f94c923cc5482f6cd8d457ab5ff3e8180c8f7cfd2c9678335d0ba56b` (existing public transformation, not official scored).

## Nonlocal crossbank Boolean cache measurement
- Obtained actual 15 × published 3357T ANGLE KMB (bank8 SHA256 `227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898`) and unchanged `submission.npz` SHA256 `d4d39b2e2516ed7c51a936e863cf0567e558a0db8ded24e435f507d76bfb78d7`.
- All 15 banks pass 1219 reachable addresses, scratch/phase symbolic checks, total CCX=3357, HMR=1543, max bank Q=128. Independent **local** verifier, not official KickMix.
- Exact 3357 live CCX product masks on all 1219 legal states: **2948 distinct**, no within-bank duplicate; 136 functions repeat across banks (409 repeat occurrences), most common appears once in all 15.
- The 409 repeats are not valid T savings: original bank contracts do not retain a crossbank cache.
- Ideal static 1-Q cache preserving only the top repeated product can save at most 14 T per pass, less than >16.2734 T needed when full chemistry T=13214, Q=405, same λ, under cost λ·Q·T. Time sharing, global scheduling changes and a different persistent-Q contract remain open.

## DQI 900Q reset-aware liveness
- Real KMB SHA256 `4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52`; **69,782,188** instructions, 900 qubits, 311858 CCX.
- 840 physical input register qubits + 60 scratch. Conservative split on R/HMR yields peak simultaneous scratch live 60, at op 20039111, thus original ordering requires the full 900Q under this model. Decoder redesign remains open.

## C45 C/B/J joint feasibility screening (model only)
- C46/3357T: λ=46.9180641, Q=405, T=13214 (6500 fixed + twice 3357).
- C45 / B129: physics errors e1=0.01973311056, e2=0.01999761702, λ=48.83615365. Across 134 generated real KMB in archived source, best actual 15-bank loader=4429T/pass.
- Assuming global Q=404 and nonloader=6500T unchanged, to improve λ·Q·T requires C45 loader **below 3113.215T/pass**. Existing best misses by 1315.785T/pass. With 4429T it would need global Q <334.776.
- This is a **sensitivity model** only; no integrated C45 official verifier run.

## Provenance, limits and artifact
- Reproducible 66-member research ZIP stored in local conversation sandbox: `GVQCC_20261123_temporal_products_DQI_liveness_BRANCH_PHASE_COUNTEREXAMPLE_RESEARCH_NOT_OFFICIAL.zip`.
- Archive SHA256: `dfb397dba88a2eab7abfa19975d1f9bcb566ccbf824eec1e105ff51cb97dd0f4`; extraction `bash REPRODUCE.sh` passed.
- Official `kickmix` native module is absent from the execution container and download attempt blocked; full official 102400 DQI / 78016 chemistry / 3133453 invsqrt verification **not run**.
- Persistent Library upload attempted, denied (`AccessDeny: id=None`). GitHub branch holds this evidence note. No new score claim.
