# Boundary repayment on the exact 17 measured adjoints

Input KMB SHA-256: 54817e9385f24940585f5a391025152d4a65a36381887ca77b7bab61413ea2ec.
Parent per-product diagnostic (#332) SHA-256: 91da349a53c2b2853513560ef2adbc2324101d4486301f97c111cece7e8bab3a.
New boundary diagnostic SHA-256: 890462cfd5e09fc17e83472aff1d5ff27d1729dc6b971932cbb9509bc9ec0ce7.

The physical compiler reconstructs the continuation frame for all 17 sites. For the 101-term interval, terms 34–50 use survivor coordinates 24–35; for each 67-term interval, terms 0–16 use coordinates 0–11 (zero-based). In the interval, measured update h and survivor update d satisfy h=Ld, checked on the emitted physical input/output coordinate map. The same mask k=L^T m applied to the survivor at both boundaries produces its delta phase for arbitrary dirty initial states. No mask parity gates per product and no private scratch. The whole tensor cannot be wrapped because other products also change those survivors.

The 36-XOR reversible classical network was found by deterministic randomized bidirectional reduction and checked against multiplication on all 4096 masks. The emitted circuit retains the reverse transform. An exact lifetime scan of the original serialized tape finds all 204 measurement outcomes subsequently read as conditions before being overwritten; none can be treated as dead (public register exclusion also checked).

Build and run from an empty experiment directory with a new/ subdirectory:
```
g++ -O3 -std=c++17 folded.cpp -o folded
./folded base.kmb quotient.tsv new/terms.txt result.kmb
g++ -O3 -std=c++17 liveness.cpp -o liveness
./liveness base.kmb physical_compile.log
```
physical_compile.log is the original #332 structural compiler log from the full research archive; no input samples or private salts used in synthesis. Relative new/ output paths are as used by that archive. The native replay comparator uses the exact 1024 distribution inputs and original RNG, saved 622, and 144 dense stress inputs. Only aggregate results are saved here. The Lean lemma source is included, but not locally compiled; #332's original Lean CI is separate.

All 17 × 8192 dirty-state C++ checks passed. Full 900Q KickMix: 1790 paired inputs, zero differences across all four counters, including exact phases; inherited union failures 411/622 and 70/144 remain. Number of instructions is 87,152,878 → 87,152,062 against #332 (816 removed), but still above original 87,067,496. Same 317,994 static paid and 316,094.000 executed mean in the original 1024 panel. This supports substituting a new nonlinear schedule without per-product phase bookkeeping; the result is not a paid improvement or a submission.
