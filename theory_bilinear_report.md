# DQI: paper-grounded bilinear contraction and exact CNOT routing

Research date: 2026-11-14. Baseline: `821_ccx480_gauge128.kmb`, SHA256
`e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7`.

## Result

The new candidate removes **9,901,509 CNOTs** through **5,199 exact block replacements**. It preserves all Toffoli gates, all 889 qubits, all classical/measurement operations, and the exact quantum map. The file shrinks from **496,089,859 to 406,976,278 bytes**, a reduction of 89,113,581 bytes. Its SHA256 is:

`3dfa80eb777a55659dcc143466d22427ccf278e198b720f24009cc921747bbcc`

This is a real circuit and storage contraction. **It does not improve the competition's Q²T objective**, because this transformation preserves both Q and T. No lower Toffoli decomposition was found in the bounded tensor searches. The complete official verifier subsequently passed **102,400 shots, with zero value errors and zero phase errors**.

| Kernel | Original CX | New CX | CCX before/after | Occurrences | Total CX removed |
|---|---:|---:|---:|---:|---:|
| GF(2¹²) product accumulator | 1,276 | 337 | 42 / 42 | 3,823 | 3,589,797 |
| GF(2²⁴) symmetric product accumulator | 6,098 | 1,511 | 99 / 99 | 1,376 | 6,311,712 |
| Total | | | unchanged | 5,199 | **9,901,509** |

The actual extracted GF(2²⁴) EEA product includes a 12-CNOT conjugation on each side. Including those unchanged outer layers, that physical block contracts from **6,122 to 1,535 CX**, with 99 CCX on both sides. Whole-file raw CNOT count is **31,294,591 → 21,393,082**.

Machine-readable evidence: `theory_bilinear_cpr_verification.json`, `theory_bilinear_manifest.json`, and `theory_bilinear_full_build.json.gz`. The compact manifest has the complete list of original-operation intervals and reductions, each template's formal certificate, input/output hashes, and the hash of the full mapping report. The gzip has every wire map and inherited condition-stack depth. All mappings are reproducible by the matcher.

Official end-to-end evidence is `theory_bilinear_official_full102400.json`, produced by the unmodified competition verifier with its full default settings:

| Official verification quantity | Result |
|---|---:|
| Verified shots | 102,400 |
| Value errors / phase errors | 0 / 0 |
| Qubits | 889 |
| Mean Toffoli count | 382,115.9631933594 |
| Repetition factor | 1.1912604648115832 |
| Reported cost | 359,753,834,625.67737 |
| Verification time | 301.1629806130004 seconds |

The verifier's reported cost is an observation for this run, not a claimed cost improvement. Every replacement preserves the Toffoli count under its inherited condition, so the underlying score structure is unchanged. The original build manifest retains its truthful build-time label that official verification was pending; the separate official result supersedes that stage without rewriting its historical hash.

## 1. Which literature actually changed the implementation

The most directly applicable paper is Khoruzhii, Gelß and Pokutta, [*Tensor Decomposition for Non-Clifford Gate Minimization*, arXiv:2602.15285v2, 26 October 2026](https://arxiv.org/html/2602.15285v2). Its bilinear-circuit and cubic-phase-routing sections apply to the three-register product accumulators here. We used its authors' **BASE** tensor decomposition implementation and **CPR** router, not the more permissive cubic-polynomial mode. CPR optimizes the CNOT realization of an existing decomposition without needing a lower Toffoli count. This is the method that produced the accepted contraction.

The author's [Polytof code](https://github.com/ZIB-IOL/polytof) is pinned to commit
`0dcac107d15adc34dc646242d222f21ae7d32699`. Its source headers were compiled without modification. The new work in this repository is the deterministic drivers, DQI tensor bridge, conjugation normalization, independent equivalence proofs, exact placement matcher, and KMB transformation. The MIT notice is preserved in `theory_bilinear_polytof_LICENSE.txt`.

[Chen and Kauers, *Flip Graphs for Polynomial Multiplication* (2025)](https://arxiv.org/html/2502.06264v1) supplied a closely related classical multiplication case: temporarily increasing the decomposition length can connect regions that fixed-length flips do not reach. We therefore tested both ordinary flip/plus walks and explicit excursions six terms above the starting length. The numerical outcomes are reported below; absence of a successful walk is not an optimality proof.

For constructive arithmetic bounds, we checked [Cenk and Özbudak, *On multiplication in finite fields*, Journal of Complexity 26 (2010), 172–186](https://doi.org/10.1016/j.jco.2009.11.002), with [official repository metadata](https://open.metu.edu.tr/handle/11511/32570), and Cenk's accessible precursor [*Results on complexity of multiplication over finite fields*, PhD thesis (2009)](https://open.metu.edu.tr/bitstream/handle/11511/18402/index.pdf). Table 5.1 of that thesis, printed page 52/PDF page 62, gives relevant constructive upper bounds. These were cross-checked against the tables and distinction between ordinary and symmetric bilinear complexity in [Ballet et al., *On the tensor rank of multiplication in finite extensions of finite fields and related issues in algebraic geometry*](https://arxiv.org/pdf/1906.07456).

The [AlphaTensor-Quantum paper](https://www.nature.com/articles/s42256-025-01001-1) is relevant context for tensor-based gate reduction, but its trained model was not used and no result from it is claimed as a measured improvement here.

## 2. Model the actual arithmetic before optimizing it

For registers a, b and z, the circuit block is an accumulator:

\[
U_F:(a,b,z)\longmapsto (a,b,z+F(a,b)),
\]

where addition is XOR and **z is arbitrary**. A bilinear decomposition of length r is

\[
F(a,b)=\sum_{i=1}^{r}(u_i^T a)(v_i^T b)w_i.
\]

Each product of the two binary linear forms can be implemented by one Toffoli. Linear preparation, output fanout, and restoration use CNOTs. A decomposition of length r therefore gives a circuit with r Toffolis, but a particular r-term construction does not prove that the tensor's minimum rank is r.

`theory_bilinear_prepare.py` imports the existing arithmetic construction and checks the resulting tensors against a separately implemented integer field oracle. It checks every input basis pair: 144 pairs for dimension 12, and 576 pairs for dimension 24. Bilinearity makes these coefficient checks sufficient for every pair of field elements.

The exact current constructions are already structured interpolation algorithms:

| Field | Existing construction in source | Decomposition length |
|---|---|---:|
| GF(2¹²) | Degree-four extension over GF(8), seven evaluation products, six binary products per GF(8) multiplication | 7 × 6 = 42 |
| GF(2²⁴) | Degree-six extension over GF(16), eleven evaluation products, nine binary products per GF(16) multiplication | 11 × 9 = 99 |

These facts are obtained from `field_tensor.py` and `extension24_tensor.py`; their SHA256 hashes are recorded in `theory_bilinear_input_certificate.json`. The GF(2¹²) polynomial is `0x1053`, i.e. x¹²+x⁶+x⁴+x+1. The GF(2²⁴) representation is GF(2¹²)[t]/(t²+t+δ), with δ=2048.

The checked literature gives μ₂(12)≤42 and μ₄(12)≤33. Composing the latter with the three-product GF(4)/GF(2) multiplier gives the **derived upper bound** μ₂(24)≤33×3=99. Another tower therefore matches the existing count; it is not by itself a Toffoli improvement. These are upper bounds, including symmetric constructions where stated, not declarations that unrestricted rank equals 42 or 99.

Changing the irreducible polynomial only changes the field basis, so it cannot reduce the mathematical minimum bilinear rank. It can change CNOT cost. A published CNOT count in a different basis must therefore include the cost of converting the surrounding DQI representation before it can be compared with the installed kernel.

## 3. A proved obstruction, with its exact scope

For each current decomposition, we formed the three paired-factor matrices whose columns are uᵢ⊗vᵢ, uᵢ⊗wᵢ and vᵢ⊗wᵢ. Exact binary Gaussian elimination gives:

| Decomposition | rank(U⊗V columns) | rank(U⊗W columns) | rank(V⊗W columns) | Distinct factors in each axis |
|---|---:|---:|---:|---:|
| GF(2¹²), 42 terms | 42 | 42 | 42 | 42 / 42 / 42 |
| GF(2²⁴), 99 terms | 99 | 99 | 99 | 99 / 99 / 99 |

This is more informative than a failed local scan. For example, write

\[
T=\sum_i (u_i\otimes v_i)\otimes w_i.
\]

If the paired factors uᵢ⊗vᵢ are fixed and independent, the coefficients wᵢ are uniquely determined. Since each wᵢ is nonzero, no term can disappear while retaining that pair-factor set. The same statement holds with either other pair of axes fixed. An invertible coordinate change preserves this independence.

**What this proves:** contractions based only on deleting an existing term by changing its remaining factor, or on a dependency among those fixed paired factors, cannot improve these particular decompositions.

**What it does not prove:** optimal tensor rank; impossibility of replacing several factors jointly; impossibility of temporarily adding terms; impossibility of optimizing a larger shared-operand block. Those require a different argument or a constructive search.

## 4. Stronger tensor search, including rank growth

Over GF(2), the following identity permits a two-term tensor fragment to be replaced by three terms:

\[
u_1v_1w_1+u_2v_2w_2
=(u_1+u_2)v_1w_1
+u_2(v_1+v_2)w_2
+u_2v_1(w_1+w_2).
\]

Here juxtaposition denotes the tensor product across the three distinct axes. Expanding and canceling the repeated terms proves the identity. Unlike a shared-factor-only scan, this move can leave the starting decomposition even when all factors are distinct.

Two finite deterministic experiments were run using the author's unmodified BASE primitives. `theory_bilinear_polytof.cpp` implements the first schedule; `theory_bilinear_depth.cpp` implements the second. Primitive counts below count **successful operations**, not merely attempted iterations.

| Field and schedule | Paths × step cap | Maximum visited length | Successful flips | Successful plus moves | Best length |
|---|---:|---:|---:|---:|---:|
| GF(2¹²), initial schedule | 32 × 1,000,000 | 43 | 28,970,810 | 3,029,190 | 42 |
| GF(2²⁴), initial schedule | 32 × 1,000,000 | 100 | 28,569,016 | 3,430,984 | 99 |
| GF(2¹²), explicit +6 bursts | 32 × 200,000 | 48 | 6,362,735 | 237,816 | 42 |
| GF(2²⁴), explicit +6 bursts | 32 × 200,000 | 105 | 6,347,119 | 331,527 | 99 |

Total: **70,249,680 successful flips and 7,029,517 successful plus moves**, with no reduced Toffoli count. The first experiment only reached r+1 despite its nominal scheduled plus calls; that limitation is explicitly recorded. The second reached r+6 and records its rank histogram. Every completed path was checked independently against all basis-pair tensor coefficients; the second experiment also checks its best decomposition.

The BASE implementation reuses dead term slots. The slot accumulation problem observed separately in the author's COMM implementation does not apply to these BASE experiments. Complete seeds, iteration caps, rank histograms, primitive counts, and best terms are in `theory_bilinear_flip_results.json`.

## 5. Where the successful contraction comes from

The original multiplier restores each temporary parity after every product. The new route keeps useful parities resident across several products and restores the three full register bases at the end. This changes the CNOT network while retaining the same number of binary products.

The actual EEA tensor also has exploitable structure. Define the conjugation

\[
C(a_0+a_1t)=(a_0+a_1)+a_1t.
\]

This is an involution implemented by 12 CNOTs from the high half to the low half of the first input register. Its action on a linear-form coefficient u is

\[
C^T u=u\mathbin{\mathtt{xor}}((u\mathbin{\mathtt{and}}4095)\ll12).
\]

For **all 99 terms** of `inverse_v2_actual_tensor99.json`, this dual conjugation maps uᵢ to vᵢ. Thus the asymmetric physical product can be normalized to a symmetric-input product, routed there, then conjugated back. This is a checked property of the actual tensor, not an assumption that every bilinear circuit is symmetric.

| Routing experiment | CX | CCX |
|---|---:|---:|
| Original actual EEA product | 6,122 | 99 |
| Direct CPR, beam width 32 | 1,814 | 99 |
| Direct CPR, beam width 1,024 | 1,673 | 99 |
| Symmetric normalization, CPR beam 1,024, including both outer conjugations | **1,535** | **99** |
| Original GF(2¹²) product | 1,276 | 42 |
| GF(2¹²) CPR, beam width 32 | 414 | 42 |
| GF(2¹²) CPR, beam width 1,024 | **337** | **42** |

This records the successive improvements rather than only the final number. The selected routes are saved as `theory_bilinear_actual_cpr.kmx` and `theory_bilinear_gf12_cpr.kmx`.

## 6. Correctness and applicability to the complete KMB

The proof uses full Boolean algebraic normal forms, with 72 independent formal variables for the GF(2²⁴) block and 36 for GF(2¹²). It compares every output polynomial, including both preserved input registers and the arbitrary initial accumulator. It does **not** assume a zero accumulator or only test random field elements. These polynomial identities cover all 2⁷² or 2³⁶ computational basis states by coefficient equality, without enumerating them. Because both circuits contain only CX and CCX, they are the same basis permutation with exactly the same phases, and therefore agree on arbitrary superpositions and entangled inputs.

Two independent reviews add evidence beyond the router's own output. `test_theory_bilinear_certificate.py` checks the full formal equivalence and rejects a candidate with a Toffoli removed. `theory_qrom_bilinear_independent_review.py` first proves a degree-two structural bound, then determines every coefficient by bit-parallel evaluation on zero, all 72 singleton inputs, and all 2,556 input pairs: 2,629 evaluations total. That independent checker does not import the router or the first ANF checker and reports equality of every output.

The whole-file matcher is conservative and exact:

1. It verifies the pinned original file's SHA256, including when a cached profile is supplied.
2. It matches the complete opcode sequence and every ordered qubit operand under one injective wire renaming.
3. No matched interval contains a measurement, phase operation, classical write, explicit condition, or condition-stack change.
4. An inherited condition stack may enclose the whole interval. The same condition either executes the entire old/new block or skips it, so the identity holds in both cases.
5. The column-splice writer checks the old operand columns before replacement and copies every nonreplaced byte column and all register metadata.
6. The resulting profile must preserve every non-CX raw gate-family count, qubit count, bit count, and the exact predicted change in instruction count.

The shared writer does not approximate source locations. Full wire mappings and original-operation intervals are recorded. Forward and reversed versions of each template have independent formal proofs; no reversed-template occurrence was found in this baseline. No unrelated transposed multiplier was rewritten without a matching template.

## 7. Reproduction

The supported route reproduction environment is **Linux or WSL**, with **Python 3.10+**, **git**, and **GCC with C++20 support** (or a compatible Clang configuration). The experiment used Python 3.12.14 and g++ 14.2.0. The existing proof module imports the Unix `resource` module, and CPR uses `__uint128_t`, so native Windows/MSVC is not covered. The bridge uses only Python's standard library and the author's vendored C++ headers; it does not require NumPy or kickmix. Optional re-extraction from the original source via `theory_bilinear_prepare.py` needs that source's original kickmix environment.

From the root of this repository, choose a new temporary work directory and obtain the exact external author source:

```bash
git clone https://github.com/ZIB-IOL/polytof /tmp/dqi-polytof
git -C /tmp/dqi-polytof checkout 0dcac107d15adc34dc646242d222f21ae7d32699
python theory_bilinear_reproduce.py --polytof-dir /tmp/dqi-polytof --work-dir /tmp/dqi-cpr-reproduction
```

The script verifies the pinned commit and that tracked author files are unchanged. It reconstructs all tensor inputs from committed certificates, checks the input hashes and conjugation identity, compiles the wrapper, reproduces all five routing experiments, proves their identities, and requires the two selected kernel files to match the recorded bytes exactly. Its compiler command is equivalent to:

```bash
g++ -O3 -std=c++20 -DVEC_WORDS=2 -I /tmp/dqi-polytof/src -I /tmp/dqi-polytof/third_party theory_bilinear_cpr.cpp -o /tmp/dqi-cpr-reproduction/bin/cpr
```

Add `--with-search` to repeat both bounded tensor searches with their recorded seeds. Their drivers compile with `-DBASE -DVEC_WORDS=1`. All subprocess arguments, input hashes and reproduced kernel hashes are saved in the work directory's `reproduction.json`. `--prepare-only` checks the committed input bridge without downloading or compiling anything. Generated proofs remain in the separate work directory.

This complete route reproduction was actually rerun in a fresh work directory: all five counts reproduced, the arbitrary-accumulator proofs passed, and both selected kernel SHA256 hashes matched byte for byte. The record is saved as `theory_bilinear_reproduction.json`.

The full candidate can be rebuilt from the pinned baseline and the committed selected kernel files without Polytof:

```bash
python theory_bilinear_patch.py /path/to/821_ccx480_gauge128.kmb /path/to/new-dqi-cpr-compact.kmb --input-certificate theory_bilinear_input_certificate.json --report /path/to/new-dqi-cpr-full-build.json
python theory_bilinear_manifest.py /path/to/new-dqi-cpr-full-build.json /path/to/new-dqi-cpr-manifest.json --gzip-output /path/to/new-dqi-cpr-full-build.json.gz
```

The output KMB must be a new file. This command cannot overwrite the baseline. The compact manifest and gzip preserve the complete review evidence without requiring a 5.6 MB pretty-printed mapping file in the main source tree.

## 8. Implication for further Toffoli reduction

The current 42- and 99-product kernels are not naive schoolbook multiplication. The checked alternative tower bounds match them, simple fixed-factor contraction is obstructed, and both shallow and explicit +6 tensor walks failed to improve them. This justifies moving a future Toffoli search toward a **different constructive decomposition or a larger joint map with shared operands**, rather than claiming that another basis change alone will reduce rank.

A useful next candidate must provide concrete new factor triples, or a larger exact input/output identity, and pass the same arbitrary-accumulator and phase checks before being inserted. The present work establishes a measured CNOT contraction and a reproducible proof/placement path that such a future lower-rank candidate can use.
