# DQI outer forward and return

## Complete twelve-wire local loan

The pinned combined DQI is `9cb3f1baf125912fc48c22813cb34e375de71b0741c02e9846aa95a4b1b04789`.
The full-word loan KMB is `9888d2b455cdf4e22f2e0dd5af1e8032c6370e644f44e5ac5b071641b68793e0`.

At each virtual source product, retain the leading coefficient in a basis
with all evaluation points except 1. Store the masked head directly into
the twelve leader data wires under the chart flag. The leader is zero on
that branch. The same conditional XOR restores the leader at the end.
Point 1 needs neither masked form and runs after the other work banks
have been released.

All 12 widths m=5…16 passed 4,096 shots each in the old and new native
fixtures. Scratch went from 24 to 12. Static cost increases by 12m+12
per site. On full production, exact Boolean replay certified all twelve
lender wires at 45 of 48 matched sites. Forty-one also passed the clean
scratch and classical boundary checks and were spliced.

| Direction | Exact replacements | Q889 cuts retired |
| --- | ---: | ---: |
| Outer forward | 23 | 646,130 |
| Outer return | 18 | 419,443 |

Every replaced span measures Q877. Global Q remains 889 with 2,912,577
Q889 cuts, versus 3,978,150 on input to this splice. Static paid gates
increase by 5,340 to 388,744. The unchanged spans keep their original
peak cuts.

The lender is the chart-zero coefficient word of each virtual product.
The original gauge data bank q852…q863 is distinct. All four snapshots
of that original bank have affine rank 12 on the same 1,024 valid end-to-end
inputs, excluding an unconditional reset at those observed cuts.

## Reproduction

Set `REPO` to the prior GVQCC checkout and `SOURCE` to Syed's
`controller_work` directory. Use the native KickMix Python.

```sh
DIR=score23_outer_word
PREV=score22_dqi_crt_phase
CENTRAL=score19_dqi_subspace/central_audit
PHASE=dqi_phase_peak

python "$DIR/virtual_lender12.py" --source "$SOURCE" --prior "$PREV" --out "$DIR/fixtures"
python "$DIR/prove_word.py" --central "$CENTRAL" --repo "$REPO" \
  --source "$SOURCE" --circuit "$PREV/dqi.kmb" --life "$PREV/lifetimes.tsv" \
  --binds "$PREV/virtual_bind.json" --out "$DIR/borrow_boundaries.json" \
  --lanes 12 --canonical-xor --timeout-ms 3000
python "$PREV/splice_loan.py" --central "$CENTRAL" --repo "$REPO" --phase "$PHASE" \
  --base "$PREV/dqi.kmb" --binding "$PREV/virtual_bind.json" \
  --proof "$DIR/borrow_boundaries.json" --fixtures "$DIR/fixtures" \
  --output "$DIR/dqi.kmb" --receipt "$DIR/loan_splice.json"
"$CENTRAL/branch_lifetimes" "$DIR/dqi.kmb" "$DIR/loans_lifetime.tsv"
ln -s ../score22_dqi_crt_phase/splice.json "$DIR/splice.json"
ln -s ../score22_dqi_crt_phase/lifetimes.tsv "$DIR/lifetimes.tsv"
python "$PREV/census_loan.py" --central "$CENTRAL" --root "$DIR" --out "$DIR/census.json"

python "$DIR/neutral_outer.py" --source "$SOURCE" --out "$DIR/neutral"
```
