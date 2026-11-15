# Combined DQI width experiments

| Tape | Global width | Width-889 cuts | Static paid gates |
| --- | ---: | ---: | ---: |
| Accepted e4 | 889 | 9,484,383 | 382,894 |
| 82 inverse-phase replacements and 34 CRT replacements | 889 | 3,978,150 | 383,404 |
| Also borrow eight dirty data wires at 41 virtual-product sites | 889 | 2,912,577 | 387,292 |

The 34 CRT prefixes were matched against every original opcode and operand.
Old and new open and closed native cases passed 34,816 shots. Each CRT
replacement retains the same classical trace. All remaining maximum-width
cuts inside the CRT splits are in the GF24 residue consume.

The virtual-product replacement holds the original leading coefficient as
a separate coordinate in a basis evaluating at all points except 1. Its
first eight wires are zero when the chart flag is one. The borrowed values
are used under that flag and then restored by reversing the swaps. Both
masked terms vanish at point 1, which runs after restoring the lender and
releasing the work banks. This reduces work width from 24 to 16 for each
native case. For m points the exact extra charge is 8m+16. Each old/new
native fixture passed 4,096 shots for m=5 through 16.

There were 48 whole virtual-product template matches. Exact Boolean
replay establishes that the eight selected data wires are simultaneously
zero on the active branch at 45 sites. Of these, 41 also passed the
conservative clean-scratch and classical boundary checks and were spliced.
Their whole-tape intervals reached at most width 881. There is no width
change in aligned untouched spans. Both experimental full tapes passed
the unchanged DQI verifier with 1,024 shots, zero value errors and zero
phase errors, using seed 7 and log2 delta −12. These experiments leave
global width 889 and add paid gates.

## Reproduction

Run from the scratch checkout containing the phase and lifetime evidence.
Set `REPO` to the prior GVQCC checkout, `SOURCE` to Syed's
`controller_work` source directory, and use the installed KickMix Python.

```sh
DIR=score22_dqi_crt_phase
CENTRAL=score19_dqi_subspace/central_audit
PHASE=dqi_phase_peak
EXP=$DIR/loan8_production
mkdir -p "$EXP"

python "$DIR/splice34.py" --repo "$REPO" --central "$CENTRAL" \
  --source "$SOURCE" --input "$PHASE/dqi_all.kmb" \
  --phase-splices "$PHASE/splice_all.json" --crt-sites "$CENTRAL/all_crt_bind.json" \
  --output "$DIR/dqi.kmb" --receipt "$DIR/splice.json"
"$CENTRAL/branch_lifetimes" "$DIR/dqi.kmb" "$DIR/lifetimes.tsv"

python "$DIR/virtual_lender8.py" --source "$SOURCE" --out "$DIR/loan8"
python "$DIR/bind_virtual.py" --central "$CENTRAL" --repo "$REPO" \
  --circuit "$DIR/dqi.kmb" --lifetimes "$DIR/lifetimes.tsv" \
  --fixtures "$DIR/loan8" --out "$DIR/virtual_bind.json"
python "$DIR/prove_loan.py" --central "$CENTRAL" --repo "$REPO" \
  --source "$SOURCE" --circuit "$DIR/dqi.kmb" --life "$DIR/lifetimes.tsv" \
  --binds "$DIR/virtual_bind.json" --out "$EXP/borrow_boundaries.json" \
  --lanes 8 --canonical-xor --timeout-ms 3000
python "$DIR/splice_loan.py" --central "$CENTRAL" --repo "$REPO" --phase "$PHASE" \
  --base "$DIR/dqi.kmb" --binding "$DIR/virtual_bind.json" \
  --proof "$EXP/borrow_boundaries.json" --fixtures "$DIR/loan8" \
  --output "$EXP/dqi.kmb" --receipt "$EXP/loan_splice.json"
"$CENTRAL/branch_lifetimes" "$EXP/dqi.kmb" "$EXP/loans_lifetime.tsv"
ln -s ../splice.json "$EXP/splice.json"
ln -s ../lifetimes.tsv "$EXP/lifetimes.tsv"
python "$DIR/census_loan.py" --central "$CENTRAL" --root "$EXP" --out "$EXP/census.json"
```
