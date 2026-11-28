# DQI: 37→32 is an expected EEA degree jump, not a unique failure signature

Date: 2026-11-27. **Research-only. No DQI repaired, no official PASS, no new score.**

## Current new user report (not independently replayed here)

- Legal error weight **33**; independent GF(4096) decoder recovers all 33 positions.
- EEA remainder degree **37→32**, a drop of 5.
- Both V111 integrated and submitted V110 extended circuit return all 70 syndrome words incorrectly; **423** of the 840 bits disagree, all work bits cleared. The same fixed input/measurement seed reproduces this case.
- The exact new 33-error NPZ, 70-word expected/actual syndrome arrays, and native measurement/branch log were **not in the available archive**. Consequently the earliest physical gate, and this case's specific confluent-field node, are not identified here.

## New independent GF(2^12) calculation on saved fixtures

Field modulus `0x1053`; primitive element `2`; 70 consecutive syndromes; legal weight `w <= 35`. The independent classical script `dqi_eea_degree_audit.py` recalculates the 70 input words from the original sparse errors; constructs the evaluator/locator; runs polynomial extended Euclid against `X^70`; and uses a **full 4095-position root scan and derivative/Forney formula** to recover the positions **and values** from the syndromes. For both newer fixtures it classifies the output residual in the exact 70-dimensional confluent-coordinate system described in the earlier V110 certificate.

| Saved fixture SHA prefix | Weight | EEA final divisor→remainder | Last quotient degree | Wrong bits (recorded) | Syndrome residual node |
|---|---:|---:|---:|---:|---:|
| `f5939fed` | 32 | 38→31 (−7) | 1 | 405 (prior separate replay) | κ=3257 (prior certificate) |
| `3da8921f` | 34 | 36→33 (−3) | 1 | 428 | **κ=4054** |
| `4809bee0` | 27 | 43→26 (−17) | 1 | 420 | **κ=3257** |

All 3 sparse inputs satisfy the key equation and permit full independent position/magnitude recovery. For the last two cases **all 70 native-returned words are wrong**, but in the invertible confluent basis **only one four-word node changes**; both infinity coordinates are unchanged. Their 70-word differences satisfy

`delta[j] = delta[j-2] XOR (kappa*kappa)*delta[j-4]`, `j >= 4`

with GF(4096) multiplication. This is a **residual-space localization**; it does not yet identify the first physical erroneous gate or imply a specific chart operation failed.

## Critical new control: 64 legal native benchmark inputs

The saved 64-input corpus has SHA-256 `6b6b99e4c8cfabd63000199eb294f377b36e369b2b1e9c9cbc4d977c888ffa80`. The original V110 native replay in the previous research bundle included 1 intentionally failing weight-32 fixture and 63 passing legal inputs (three measurement seeds). Running the **independent classical EEA** over the 64 shows:

- **64/64**: the final degree drop equals `71 − 2w`.
- **62/64**: the final degree drop is at least three.
- **Five weight-33 controls** (`indices 10,29,31,47,61`) each have **37→32 (−5)**, while the saved native replay records them as passing.
- Only the intentionally failing weight-32 example has the `u3=0` nonterminal fourth reciprocal condition among the first four head snapshots of this corpus; all five weight-33 controls have a nonzero `u3`.

Mathematically, with `S(X)=sum_{j=0}^{69} S_j X^j`, `a_i=2^{p_i}` in GF(4096),

`Lambda(X) = product_i (1 + a_i X)`

`Omega(X) = sum_i e_i a_i * product_{h != i}(1 + a_h X)`

we have `S Lambda ≡ Omega (mod X^70)`, `deg Lambda = w`, `deg Omega <= w-1`. When the Euclidean remainders descend one degree at a time until degree `70-w`, and the final remainder has degree `w-1`, the last drop is exactly

`(70-w) - (w-1) = 71-2w`.

**Thus the jump itself does NOT explain native failure.** In particular, `37→32` is compatible with many correctly decoded weight-33 samples, and it does not mean the final quotient has degree five (our three failing fixtures all have *linear* last quotients).

## Narrowed investigation for the new weight-33 input

1. Feed that fixture's `syndromes` and `actual_syndromes` to `dqi_eea_degree_audit.py` and compare the 17 nodal four-word blocks and two infinity words. Determine whether the 423-bit residual also occupies exactly one κ block; do not infer this from its bit count alone.
2. At the first invalid κ, compare the **nonzero-input contract** for the 24-bit reciprocal; capture operand, GF(2^24) norm, zero flag, carry, active/stop flag and measurement bit before and after the division. A zero input with a nonterminal numerator is a finite-chart pole, even though `inv0(0)=0` is a correct arithmetic subroutine.
3. Confirm EEA correctness with independent `r_{i-1}, r_i, quotient, remainder, t_i` through the stop crossing. A correctly computed degree jump is not the first bad native gate. Record logical branch identity and absolute KMB operation/HMR index once the first mismatch appears.
4. Prove both forward restoration and reverse/HMR phase for every relevant branch before a new native patch is submitted. A zeroed ancilla register **does not** establish correct logical output or phase.

Current classification: **NORMAL_EEA_DEGREE_DROP / NODAL_RESIDUAL_REPRODUCED_FOR_OLDER_FIXTURES / NEW_W33_NATIVE_FIRST_GATE_UNKNOWN.**

## Reproduce without modifying any real KMB

```
python dqi_eea_degree_audit.py inherited_batch345_shot195.npz \
  v110_default_batch158_shot179.npz v110_default_batch261_shot223.npz \
  --corpus dqi_64_legal_inputs.npz --out degree_audit_results.json
```

The exact four NPZs are sourced by name/SHA from the earlier V110 research ZIP and are intentionally **not embedded in this GitHub addendum**. Their contents remain in the owner's saved research material.