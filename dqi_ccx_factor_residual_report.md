# Residual input-side Toffoli factorization scan

**No additional rewrite was found.** The complete scan finished in 23.883 seconds with maximum RSS 223,636 KiB (218.4 MiB). No candidate was written and no full circuit simulation was run.

## Input and the two specific search gaps

The input was the already verified, unchanged `821_ccx480_gauge128.kmb`, SHA-256 `e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7`.

The earlier input-factorization pass searched a 256-instruction window and retained only the latest gate for each `(target, shared control, explicit classical condition)` signature. It also required one gate to commute all the way to the other gate's position.

This one additional read-only scan used a 4,096-instruction window, considered **every prior matching signature inside that window**, and allowed **both gates to move to a shared intermediate position**. For an intervening sequence `M`, a split `k` is valid when the first CCX commutes with `M[:k]` and the second with `M[k:]`. This includes both endpoint moves and central meetings.

The identity remains:

```text
CCX(a,b,t); CCX(a,c,t)
  = CX(b,c); CCX(a,c,t); CX(b,c)
```

All four quantum wires must be distinct, the two explicit conditions must match, and the existing conservative commutation checks remain in force. Measurement, reset, classical writes, condition-stack changes, and other unsupported instructions are barriers. The scan never crosses one of those barriers.

## Complete scan counts

| Quantity | Count |
|---|---:|
| Remaining CCX instructions scanned | 363,694 |
| Prior matching-signature pairs considered | 2,248,772 |
| Pairs satisfying the four-distinct-wire identity | 213,204 |
| Pairs admitting a valid commutation split | **0** |
| History resets at intervening barriers | 49,840 |
| Additional CCX reduction | **0** |

The process was limited to a 1 GiB address space and a 240-second scan budget. It completed well within both limits. It parsed compact binary columns with memory mapping, without constructing a native Kickmix circuit or millions of Python gate objects.

## Interpretation and stopping point

The broader ordering and window search found no residual opportunity for this particular input-side factorization identity on the current candidate. This does not establish global optimality and does not cover larger windows, more general linear-basis changes, different circuit identities, or algorithmic resynthesis.

The requested bounded experiment is finished. There is no replacement candidate to verify or submit, and no further search was started.

Reproduction:

```bash
python gvqcc_repo/dqi_ccx_factor_residual_scan.py \
  dqi_inputs/821_ccx480_gauge128.kmb \
  --report gvqcc_repo/dqi_ccx_factor_residual_e986.json \
  --window 4096 --seconds 240
```

The JSON records the input hash, script hash, complete scan status, resource use, and all counters. Existing candidate and worker files were not modified.
