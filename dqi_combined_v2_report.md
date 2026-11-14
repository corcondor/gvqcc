# DQI candidate v2: 480 exact CCX removals plus the expanded gauge

This is a separate candidate. The previously pinned `aafed8b0...` circuit, its reports, and the v1 reproduction pipeline are unchanged.

## Full default local verification

The candidate passed the unchanged competition verifier on all 102,400 default samples with zero value errors and zero phase errors.

| Metric | v2 candidate |
|---|---:|
| Qubits | 889 |
| Classical bits | 154,799 |
| Static Toffoli-like count | 382,934 |
| Mean Toffoli-like count | 382,115.5671582031 |
| Value errors / phase errors | 0 / 0 |
| Repetition overhead | 1.1912604648115832 |
| Local resource cost | 359,753,461,767.22644 |
| Reaction depth | 40,891 |
| Instructions | 59,378,866 |
| Verification time, one worker | 344.63 seconds |
| Peak resident memory | 4,750,136 KiB |

Candidate SHA-256:

`e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7`

The verifier used its default empty salt, default circuit-hash-derived seed, batch size 256, and confidence parameter `log2_delta=-128`. The local cost is 0.12671604% below the public baseline's separately sampled published default cost of 360,209,905,486.0156. This is a local result, not a confirmed Kaggle leaderboard score.

The flat native result is `dqi_combined_v2_full_verification.json`.

## Completed paired comparison

The unchanged baseline was then evaluated on exactly the same 102,400 sampled inputs and simulator batch seeds. Both circuits passed with zero value and phase errors, giving the same repetition overhead.

| Same-input full comparison | Unchanged baseline | v2 candidate |
|---|---:|---:|
| Mean Toffoli-like count | 382,599.9932617188 | 382,115.5671582031 |
| Static Toffoli-like count | 383,414 | 382,934 |
| Value errors / phase errors | 0 / 0 | 0 / 0 |
| Repetition overhead | 1.1912604648115832 | 1.1912604648115832 |
| Local resource cost | 360,209,538,364.6973 | 359,753,461,767.22644 |
| Qubits | 889 | 889 |

The measured saving is **484.426103515625 Toffoli-like gates per shot**: 480 from the two exact peephole transformations and 4.426103515625 additional mean saving from the gauge expansion. Paired resource cost falls by **0.1266142478%**, or 456,076,597.4709 cost units. The paired baseline took 297.63 seconds with one worker.

The flat baseline report is `dqi_baseline_v2_paired_verification.json`. The combined comparison and exact aggregate gate-count differences are in `dqi_combined_v2_paired_comparison.json`; per-block rewrite certificates and polynomial proofs are in `dqi_input_factor_v2_proof.json`.

## Changes and exact local proofs

The first change, already present in v1, combines same-control CCXs with different targets:

```text
CCX(a,b,x); CCX(a,b,y)
  = CX(x,y); CCX(a,b,x); CX(x,y)
```

It removes 96 unconditional CCXs.

The new input-side rule combines CCXs with one common control and the same target:

```text
CCX(a,b,t); CCX(a,c,t)
  = CX(b,c); CCX(a,c,t); CX(b,c)
```

Here `a,b,c,t` must be distinct. The target changes by `a*b XOR a*c`, and every other register is restored. Both sides are the same basis-state permutation without phase, so the equality holds for arbitrary quantum states, including states entangled with other registers.

The new rule removes 384 additional CCXs in 16 blocks. Each 36-CCX block becomes 12 CCX plus 48 CX. These blocks are disjoint from the old 96-removal blocks. All have condition-stack depth zero and no explicit classical condition. Consequently the combined peephole changes remove exactly 480 Toffolis per shot without adding quantum bits.

Every gate moved during a rewrite is checked for commutation with each crossed current gate. Measurements, resets, classical writes and condition-stack changes are barriers. Newly inserted CNOTs are included in subsequent checks. Each complete new block was also verified independently as an equality of Boolean polynomials on 27 input variables, covering all 134,217,728 basis assignments without enumerating them. Five regression tests cover the basic 16-state identity under both classical conditions, reversed control ordering, interleaved three-bank blocks, ordering barriers, and rejection of an incorrect rewrite.

The existing 128-label classical gauge is retained. Its 64-label original choices remain available, and strict capped-count comparison ensures that expanding the choices cannot reduce the number of zero scan masks. Phase compensation and mask restoration include the seventh label bit. Its exact contribution to the mean gate saving is reported by the paired comparison, separately from the 480 unconditional removals.

## Reproduction of the additive step

```bash
python dqi_ccx_input_factor.py 821_ccx_gauge128.kmb \
  --output 821_ccx480_gauge128.kmb \
  --report 821_ccx480_gauge128.report.json

python -m unittest test_dqi_ccx_input_factor -v

python verify_dqi_candidate.py 821_ccx480_gauge128.kmb \
  --verifier verify_submission_dqi.py \
  --output 821_ccx480_gauge128_full102400.json
```

The input to the additive step must hash to `aafed8b0fa2bbfde21f47672a5e548a84a6d42d735e800557efbb2c04c310f09`. The tool refuses an existing output file. It validates the original and rewritten binary formats, verifies the exact bytes of rewritten spans, and copies untouched registers and instructions verbatim.

For the paired unchanged baseline, the explicit seed is:

```text
105627115000454673480560843138090279010582148233824853720275839910719324590759
```

This is the candidate's normal default seed, fixed by its actual circuit hash. No no-op changes, alternate salts, or searches for favorable verifier samples were used.

## Provenance

Verifier SHA-256: `f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65`.

Local engine: official PyPI `kickmix==1.0.0`, Python 3.12. Engine binary SHA-256: `d965e0ad42e7e3a147d4b28d6971a517f772dd79795cfc364be2fe9ffe3a7b80`. The competition-bundled engine is a separate environment and should be recorded independently when used.

The compiler research connection and primary IBM/Microsoft links are in `research_dqi_ibm_microsoft.md`. Existing public-source attribution remains applicable to the unchanged decoder and expanded gauge.
