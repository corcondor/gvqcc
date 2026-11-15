# Rolling-tail extractor checkpoint schedule

Starting tape `score22_dqi_crt_phase/loan8_production/dqi.kmb`, SHA-256
`3e50000e18f2f1746de3270cf88c10d7b6ea3f577988a3cd13ba1f90a8da48e2`.

The 24-input zero check and masked zero phase previously held a 22-wire
AND chain. The rewrite computes a checkpoint for the first ten inputs,
releases its intermediate nodes, and reuses those wires for the other
fourteen inputs. After the result is consumed, an X-basis HMR releases the
checkpoint and its outcome controls the short phase repayment. The target
of the zero XOR may contain either bit before the check. This depth-first
schedule uses 14 helper wires. It adds eight static Toffoli in the
conditioned phase repayment for the first segment.

A binary matcher located 33 XOR checks and 17 masked phases inside the
two extractor callers. A classical-use proof traverses each old scratch
ID's subsequent references and joins the executed and skipped states
at each original condition boundary. Every read must follow a dominating
ordinary overwrite on its executed arm. This established that the
old IDs can be retired at all 50 sites. Replacement scratch uses 14
physical names from the exact original module's 22 owned clean helper
wires. Selecting those names uses the original lifetime profile and
requires no inference of cleanliness from idleness.

| Actual changed regions | Sites | Maximum width before → after |
| --- | ---: | --- |
| Extractor forward | 16 | 888 → 880 |
| Extractor forward | 1 | 887 → 879 |
| Extractor return | 1 | 889 → 881 |
| Extractor return | 16 | 888 → 880 |
| Extractor return | 15 | 887 → 879 |
| Extractor return | 1 | 886 → 878 |

The branch-sensitive fixed-order profile records 42→0 cuts at width
888 or greater and 1,376→1 at width 881 or greater within the changed
sites. Whole-circuit width remains 889. This is a local result across
the 50 matched subroutines. The remaining extractor arithmetic retains
the whole width.

The four local reference and replacement cases each passed 16,384
native shots. The scheduled whole tape passed 1,024 shots in the stock
DQI verifier with zero phase or value errors (`seed=7`, `log2_delta=-12`).
Static Toffoli increased by 400. The measured mean increased from
386,463.33 to 386,631.84 for these paired smoke settings. The whole tape
is a research intermediate and does not improve the score.

## Reproduce

Set `SOURCE` to the upstream `controller_work` directory, `GVQCC`
to the prior repository checkout, and `VERIFY` to the unmodified DQI
verifier. Run with the matching KickMix installation.

```sh
DIR=score23_dqi_tail
BASE=score22_dqi_crt_phase/loan8_production
CENTRAL=score19_dqi_subspace/central_audit
mkdir -p "$DIR/scheduled"
python "$DIR/checkpoint.py" --source "$SOURCE" --out "$DIR/native" --split 10
python "$DIR/bind.py" --central "$CENTRAL" --prior-code "$GVQCC" \
  --source "$BASE/dqi.kmb" --source-lifetime "$BASE/loans_lifetime.tsv" \
  --loan-receipt "$BASE/loan_splice.json" \
  --callers score22_dqi_peak/combined/caller_ranges.tsv \
  --native "$DIR/native" --schedule-helpers --out "$DIR/scheduled/bind_full.json" \
  --output-kmb "$DIR/scheduled/dqi.kmb"
"$CENTRAL/branch_lifetimes" "$DIR/scheduled/dqi.kmb" "$DIR/scheduled/lifetimes.tsv" \
  > "$DIR/scheduled/lifetime.json"
python "$DIR/coverage.py" --central "$CENTRAL" --source "$BASE" \
  --candidate "$DIR/scheduled" --out "$DIR/scheduled/coverage.json"
python "$VERIFY" "$DIR/scheduled/dqi.kmb" --num-shots 1024 --batch-size 256 \
  --max-workers 4 --seed 7 --log2-delta -12 > "$DIR/scheduled/verify.json"
```
