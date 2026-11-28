# 2026-11-23: Reversible arithmetic / clean-ancilla pebbling integration

**No score improvement.** This is an executable source and isolated binary-KMB integration, not a verified replacement of an existing invsqrt, DQI or ANGLE circuit.

## New code (package under `research/griffith_qcc/`)

- `src/griffith_qcc/reversible_blocks.py`: reversible 3:2 CSA (2n CCX, 3n CX, 5n qubits), modulo-2^n ternary Cuccaro-style adder (4n-4 CCX, 9n-4 CX, 4n+1 qubits for n>1), AND multi-output fanout (1 CCX for simultaneous uses), clean AND cache (2 CCX for separated uses), classical exact permutation simulator.
- `src/griffith_qcc/pebble_schedule.py`: Dijkstra reversible pebbling on small AND DAG cuts. Minimizes actual CCX computes/uncomputes under fixed clean-ancilla budget; gates use CX/CCX only, and clean scratch returns to 0.
- `src/griffith_qcc/kmb_export.py`: native KMB format-v2 serialization of X/CX/CCX blocks; fails closed for unsupported HMR/phase operations.
- Three new `tests/test_{reversible_blocks,pebble_schedule,kmb_export}.py` files. The user's standalone production-style KMB parser independently re-read eight emitted binary KMBs and checked every operation and register.

### Proven tests / source run
- 3 inputs x 4 bits => **4096/4096 basis inputs** passed for both CSA and final modulo sum, including input conservation and full reverse cleanup.
- Arbitrary dirty *output targets* were exhaustively tested for the one-CCX fanout. The clean cache is restored exactly; this does not permit dirty **cache** ancilla without further proof.
- 4-bit CSA: 20Q / 8 CCX / 12 CX but outputs S and K, so not comparable to a completed integer sum.
- 4-bit modulo ternary sum: 17Q / 12 CCX / 32 CX with all A,B,C preserved. No overflow output.
- AND DAG `v0=a&b; v1=v0&c; v2=v1&d`, XOR `v2` to result: 3 clean anc => 6 CCX; 2 clean anc => 8 CCX, clean in both cases. Minimizing Q alone would miss the Q^2 T tradeoff.
- Local read-only KMB opcode scans (public V8 ANGLE 15 × 128Q + 37Q invsqrt) found **zero contiguous MAJ/UMA/CSA templates** and zero stricter nonlocal disjoint-commutation MAJ/UMA for invsqrt, bank0 and bank1. The loaded V8 3375T is older than public 3357T; do not use it as frontier benchmark.
- Original V8 / invsqrt files were not modified. No official native verifier run, no Kaggle submission.

### OSS sources and applicability
- [Google Qualtran GF2 arithmetic](https://github.com/quantumlib/Qualtran/blob/main/qualtran/bloqs/gf_arithmetic/gf2_multiplication.py), Apache-2.0: **study** for DQI. Production GF(2^12) multiplicative kernel is already **42 CCX**, so replacing it with generic Karatsuba (63 CCX for n=12) would be a regression.
- [ETH Reqomp](https://github.com/eth-sri/Reqomp), MIT; [Paradis et al. 2024](https://doi.org/10.22331/q-2024-02-19-1258): small-DAG clean-ancilla scheduling idea, independently implemented here without Qiskit.
- [Cuccaro et al. 2004](https://arxiv.org/abs/quant-ph/0410184): ripple MAJ/UMA integer addition, independently written.
- [Gidney 2018](https://doi.org/10.22331/q-2018-06-18-74): measurement-assisted temporary logical AND cleanup. **NOT implemented here**; existing GVQCC compiler already uses HMR and phase corrections, so cannot blindly delete uncomputation.
- [Liu, Zhou, Meng 2026](https://arxiv.org/abs/2608.09578): clean/dirty uncomputation research, not automatically borrowed because its phase and dirty-state model requires integration checks.

### Reproduction
Original research ZIP in the 2026-11-23 conversation: `GVQCC_OSS_Reversible_Cuccaro_Reqomp_Integration_20261123.zip`, SHA-256 `d083f9fb4262fe85d442f7469d762bf34e678f26a20a40e1bd993e388e2d8f07`. It contains: all source files, local tests, eight standalone KMBs and KMx files, and source KMB audit. Native KickMix not available in the local interpreter.

To test the GitHub module on PR17:
```sh
python -m pip install -e "research/griffith_qcc"
PYTHONPATH=research/griffith_qcc/src python -m unittest discover -s research/griffith_qcc/tests -p 'test_*.py' -v
```

**Next production gate:** Extract an *actual* arithmetic / temporary-value DAG from the latest scored KMB (not a gate-pattern guessed solely from local examples). Replace it, prove full value + phase + workspace over the cut, measure `Q_peak,T_mean`, and then run unchanged official verifiers. No numerical score claim until that succeeds.
