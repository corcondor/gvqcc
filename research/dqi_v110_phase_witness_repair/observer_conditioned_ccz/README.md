# Observer-conditioned Clifford substitution on the 316094 baseline

Starting point: corcondor/gvqcc PR #331 (exact abstract Boolean live-value relations); this version adds a solver restricted to the observer branch and a directly observer-weighted phase span. It cannot assume that the controls are independently distributed.

For a CCZ with controls a, b, c, reduce the live-wire expressions under the original guards and c = 1, then test whether a*b lies in their affine GF(2) span. The solver may re-expand earlier Boolean products to propagate the observer condition inside them. An alternate solver uses c, c*w_i and the original guard directly. Gaussian elimination uses actual sorted atom sets. The returned support is independently recomputed by XOR of the original columns and compared exactly. There is no sampled certificate. A lost symbolic expression is only replaced by a fresh abstract atom; resource bounds can produce false negatives. Solutions require <=8 emitted Cliffords.

Usage: g++ -O3 -std=c++17 live.cpp -o live; ./live base.kmb out.kmb unitary pairs . The unitary mode creates no new HMR outcomes or qubits. The scanner is fail-closed on unsupported opcodes. The saved input hash is 54817e9385f24940585f5a391025152d4a65a36381887ca77b7bab61413ea2ec.

Regression: g++ -O3 -std=c++17 regression.cpp -o regression; ./regression . The full native local regression is python3.12 check_observer.py ./live with KickMix 1.0.0. For each of a guarded and unguarded instance, 256 shots exhaust both guard values and all 128 quantum input assignments. Both instances removed the intended CCZ (7→6 paid), preserving all physical qubits, the public classical bit, and absolute phase. This is not a full DQI result.

ObserverPhase.lean states the parity distribution and guarded phase identities; Lean compilation is not claimed unless shown in a receipt. It does not prove the C++ symbolic engine.

Full-tape receipt: all 6,686 CCZs inspected in all three observer orientations with two tests per orientation, for 40,116 calls. Zero substitutions by either test. The 900Q output is byte-identical to the 87,067,496-op input with 317,994 static paid gates. No new sampling or official score claim; the matched 1,024-shot 316,094.000 value is the previously measured baseline, not a new gain. The exact negative is limited to this bounded search.
