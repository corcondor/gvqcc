# Degree-71 candidate-independent phase and in-place ghost filter

Existing component sources: #338 (included hankel_s71.py for exact convention), #334/#339 (ghost filter, rectangular rank proof). The EEA-derived Padé denominator from the original 70 moments, the dense independent-dual reference H*l=sqrt(diag H), and true sparse moments agreed over 360 field cases, including 350 singular cases. The EEA multiplication counts are classical nontrivial products, exclude inversions and reversibility, and are NOT physical cost. The explicit 35-root wrong locator reproduces S71=457 while having 35 nonzero residual words. It is not accepted. Full residual admission is preserved.

The separate native `Tr(sqrt(gamma)*sum l_i*b_i)` contract assumes two simultaneously live, disjoint word banks and CLASSICAL gamma. It uses 23 reusable classical forms indexed by i+j, no output word and zero paid gates; six widths, 512 tests each with value, public bits and phase checked. At d=35: 840Q across those two banks, 5,176 instructions. No coherent solver or physical bank placement is supplied.

The in-place #334/#339 ghost filter preserves the initial 18 words and writes 52 filtered words over the other 52. It compiles in descending order by output, reverses with the reversed gate list, uses 840 occupied input qubits, zero scratch, zero paid, and 41,496 CNOT each direction. Both circuits were serialized and read back in KickMix SDK 1.0.0. All 1,280 forward + roundtrip cases (including 576 legal/ghost pairs and 128 arbitrary dirty rows) preserved expected values and absolute phase. Rectangular rank was checked classically, not emitted. Neither component is a full 900Q patch or a new competition score.

Reproduce on supported Python with KickMix 1.0.0 and NumPy:
```
python structured_phase.py > structured_receipt.json
python filtered_native.py > filter_receipt.json
```
