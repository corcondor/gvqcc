# DQI numerator: in-place monic reduction and conditional HMR cleanup

Two distinct experiments on the pinned physical seam from #261. Neither implements the missing in-place (A_{
m raw}^{-1}mod B) or a complete native half-coordinate adapter. No updated competition score.

## In-place reduction by a monic degree-17 divisor

Early normalization supplies monic (B=X^{17}+B_{lo}) in square-coefficient form on the odd D words. Keep the leading words P17 and A17 where they are. Adding (P_{17}B_{lo}) to P's lower coefficients gives (Pmod B); adding (A_{17}B_{lo}) gives (Amod B). The odd N sector needs no reduction because its degree is at most 16. The same formula applies in the squared frame by characteristic two, so inverse Frobenius is not needed for this step.

The field update is a 42-CCX product with separate CNOT frames on each operand and on the target. Execute the frames on a shared scalar once, not once per coefficient, and share B frames between sectors when both reductions are scheduled together. The circuit is an involution on arbitrary words and touches no added coherent workspace at the 865-wire seam.

| Native mode | Instructions separately | Instructions shared | CCX / paid |
|---|---:|---:|---:|
| Numerator alone | 8,670 | 6,270 | 714 |
| Locator's even sector and numerator together | 17,340 | 10,194 | 1,428 |

Every circuit passed 1,024 randomized all-wire KickMix cases forward and 1,024 reversed. These are prices for the step if the final adapter needs these residues, not savings against a full adapter. In particular, do not blindly add the residue and original degree-17 product costs if a later product has already fused the step.

## Two-coefficient conditional erasure

Given surviving witnesses satisfying (P_{raw}=A_{raw}U+BZ) (or (Q_{raw}=A_{raw}T+BW)), clear two low coefficients. HMR creates one classical mask per coefficient. Reuse the classical adjoint reduction mask across all products contributing to that coefficient. The correction uses only CX, classical bit operations and CZ conditioned on the HMR record. The high numerator word N34 is a spectator and survives.

The circuit uses CBIT outputs for the measurement test. Production composition must clear those records after using them (classical-only). This coupon places the surviving coordinates on D,N coefficient wires and has two *redundant* old words on q865–q888 as inputs. It does **not** show that full old and new numerator vectors and both witnesses can coexist. All live 865 inputs, including N34, are checked.

| Mode, per sector | Q | CCX / actual paid | Instructions | CZ |
|---|---:|---:|---:|---:|
| Arithmetic undo | 889 | 252 | 3,060 | 0 |
| HMR with shared reduced mask (selected) | 889 | 0 | 1,020 | 864 |
| HMR with adjoint rank-42 tensor | 889 | 0 | 5,028 | 252 |
| HMR with two-term Karatsuba frames | 889 | 0 | 1,230 | 864 |

All six corrected HMR circuits passed 2,048 valid shots each. On 512 additional shots per corrected circuit the redundant numerator was deliberately wrong; the observed phase matched the fault dot the *actual* measurement record, not an expected zero. The uncompensated HMR control produced 1,051 and 1,019 phase flips out of 2,048 respectively, confirming that the test detects unpaid phase debt. Lower CZ count in the tensor variant did not outweigh its CNOT overhead.

## Reproduce

Set PYTHONPATH to include the pinned `research/dqi316k_joint_crt` source at #261 head `bf87158c58b5f183f08798d6d449e42c10177019`, with KickMix 1.0.0 and NumPy. In a writable copy with the same sibling paths:

```sh
ln -s ../phase261/raw_audit.json raw_audit.json
python repay.py
python monic_reduce.py
lean -DwarningAsError=true NumeratorErase.lean
```

The Lean lemmas certify local XOR and phase repayment given the product witness, not the witness generation or the full circuit. The actionable next step remains a reversible quotient-ring division acting on the existing lower numerator wires, without a separately materialized degree-17 old/new vector.
