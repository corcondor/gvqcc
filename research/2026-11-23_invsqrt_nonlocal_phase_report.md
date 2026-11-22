# GVQCC 2026-11-23: independent nonlocal invsqrt phase-gadget synthesis

**Status: research candidate only; no official KickMix/Kaggle verification, no certified score change.**

## Starting artifacts

- Parent 18-file ZIP SHA256 `abd3a84932cd479829f55d01ce73c4af85cf8fa2a2f38b56f8cc5813a3b275f6`, corresponding to `GVQCC_33p135213091_joint_W_H2_CANDIDATE_UNVERIFIED_20261122.zip`. The nominal 33.135213091 value is **unverified**.
- Source `invsqrt.kmb` SHA256 `d2148a7cd7a4d0a004eca1e7b18f9fd1282df4ed3be4a9aa970842f9119fa307`, 37 qubits, 1470 CCX.
- Audited parent chemistry `submission.npz` SHA256 `7c989e42408a8595aa92e55464f9dd2d17b91963b359f1dd899da329d90f6997`; independent FeMoCo reconstruction: error1 `0.01999999999296163`, error2 `0.019999999950658907`, lambda_eff `46.918063987784784`, gap `3.9148980001191376`. Numerical conditions pass; full official combined test not run.

## Independently discovered nonlocal identities (not a published loader transplant)

The native invsqrt KMB has two different late triples of conditional quarter-turn phase support that can be rewritten using **earlier, already computed wires**. On the entire official x domain (0 to 3,133,452), a packed-bitset execution of every classical operation before the last edited phase shows:

1. Original operation indices `32662, 32663, 32665` (three non-Clifford `Z_POW(±π/4)`) can be **deleted together** and replaced by `Z_POW(+π/2)` on q36 immediately after original op index `8344`.
2. Original operation indices `34341, 34342, 34344` can be deleted together and replaced by `Z_POW(+π/2)` on q35 immediately after original op index `8145`.

This is phase polynomial resynthesis **across more than 25k intervening operations**, including nonlinear classical computations; simply merging neighboring CCX cannot produce it. It removes **six T-type rotations and inserts two S-type rotations**, with no new CCX and no width change. Algebraically the 3T parity gadget obeys `f_a XOR f_b = f_c`, and the phase sum `π/4(f_a+f_b-f_c)=π/2 (f_a AND f_b)`. At an earlier time the product function is already present on an existing wire. The equality is on the specified input domain, not on arbitrary 22-bit values.

Additionally incorporated *previously published* varianceofx 3T->2S edit: delete original indices `223,232,234`, insert `Z_POW(-π/2)` on q31 after index `10063` and `Z_POW(+π/2)` on q33 after `21002`. **Do not count that third gadget as a new discovery.**

## Candidate and proof

The combined, actual KMB binary has SHA256 `f9f00359d591bb0c9ec07d8d216efcc6086521ccd123f00796e0a6f84bd52452`, 37Q, 1470 CCX, and source-to-candidate 60,767 -> 60,762 ops; 56 -> 51 Z_POW rotations. Changes: **9 T-type rotations deleted / 4 Clifford S rotations inserted**. This is *not* a nine-Toffoli saving.

A separate source-operation audit showed 60,758 pre-existing operations and 47 pre-existing phase angles remain identical. Full 3,133,453-input modulo-eight phase differential:
- Combined 9T->4S: `[3133453, 0, 0, 0, 0, 0, 0, 0]` (0 mismatches).
- Novel 6T->2S alone: same.
- Wrong-sign S negative control: **749,964 phase mismatches**.
- 22-bit **out-of-domain** control: 6 mismatches (starting x=3145728), showing the claim has a precise domain.
- Up to and including last edited operation 34344, **no classically conditioned classical-data gate** occurs; accumulated relative phase is *already zero* there on every supported input. The first conditioned data gate occurs at op 35378; later conditioned operations and HMR/phase feedforward therefore cannot distinguish the circuits. This proves the differential phase for every measurement branch *relative to the original parent*. It does not independently verify the parent's absolute phase against the required analytic function.

The new 18-file ZIP `GVQCC_33p135_nonlocal_invsqrt_9T_UNVERIFIED_20261123.zip` SHA256 `445d03f912d0c9f1095f71c9cb46268e81ac4cd409b58ed77c7d3a03e83975d4`. Only `invsqrt.kmb` changes; the other 17 entries are byte-identical to the parent.

## Source and reproduction

Reproduction entry point committed on this branch: `research/invsqrt_nonlocal_phase_patch.py`. Uses `kmb_profile.py` and `dqi_ccx_peephole.py` already in this repo; it rejects any input whose SHA is not the pinned original. Run

```bash
python research/invsqrt_nonlocal_phase_patch.py invsqrt_original.kmb invsqrt_nonlocal_candidate.kmb
```

Expected output SHA `f9f00359…`. An independent standalone research ZIP containing original and candidate KMB files, the bit-sliced differential checker, complete receipts and negative controls was generated, SHA256 `5aee6cb6ad305afae331e1743a72897f8e0d8c51d0cc83983b8f9cdde4ab004b` (`GVQCC_20261123_nonlocal_invsqrt_9T_original_phase_proof_RESEARCH.zip`). These local artifacts are **not part of the Git repository**.

No `kickmix` or Kaggle verifier package was installed in this execution environment and network download was unavailable. Therefore: **no official value/phase test, no official aggregate cost, no verified record.** The original score baseline **33.13521306472748** remains the comparison target. Complete native KickMix and competition scoring required before claiming an update.

Library persistence attempt on 2026-11-23 failed with `AccessDeny`; repository research branch is therefore the durable source record. No main-branch changes or user competition submissions were made.
