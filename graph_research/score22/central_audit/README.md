# DQI production CRT split and central width census

Baseline KMB `e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`.
This has 58,868,734 executed instructions in the KMB tape and a static width of 889.

## Component binding

The census binds exact opcode and operand patterns from the source `_adjoint_consume`,
ordinary GF24 consume and scalar GF12 consume. It then intersects the hit ranges with
fresh branch-sensitive lifetimes. Indices are zero based and interval stops are exclusive.

| Width in the pinned order | Positions | Adjoint GF24 sites | Ordinary GF24 sites | Positions inside either GF24 template | Positions outside both |
| --- | ---: | ---: | ---: | ---: | ---: |
| 889 | 9,484,383 | 98 | 64 | 881,728 | 8,602,655 |
| 881 or greater | 10,274,028 | 113 | 79 | 1,189,820 | 9,084,208 |

At width 881 or greater, 558 exact scalar-consume sites cover a further 738,752 positions.
Even ideal local substitutions in all three template families leave 8,345,456 positions
in the fixed schedule. These counts describe a conservative fixed-order bit-constant
profile. They do not establish a global width lower bound.

## Split the longest polynomial synthesis update

The longest outside-GF24 run belongs to `fused_crt_synthesis.emit_prefix` with
`r=34, i=0`, exactly matched at `[26074636,26452636)`. It computes
`C = q_i N + P D` while holding a two-word temporary, used as an output basis
with `N`, across all 36 scalar points.

The replacement computes the 34 scalar evaluations of `C` directly in existing
`N` words. Multiplication by `q_i` at these public points is an invertible
linear basis change. The remaining CRT coordinate is the quadratic residue
`C(alpha_i) = P(alpha_i) D(alpha_i)`, consumed in the original P register.
It produces the same 24 old-P measurement masks in the common field basis.
An inverse CRT change returns the coefficient representation expected by the
untouched closing block.

- The four native circuits for each of r=5 and r=34 checked every output word
  against the polynomial formula and checked uncompute, random probe phase
  and scratch. Each circuit ran 2,048 shots.
- The degree-34 component was spliced into the exact pinned production site.
  The byte columns outside that site, the original registers, and all mask IDs
  were preserved. The splice adds 15 unconditional CCX and removes 6,845 ops.
- The local number of width-889 lifetime cuts dropped from **373,046 to 5,057**.
  Every remaining cut of width 881 or greater within the changed block lies in
  a single 6,245-op GF24 residue consume. Whole width stays 889.
- The spliced tape serves as a research intermediate. A stock DQI verifier
  run and a score improvement are outside the receipts here.

## Reproduction

Set `EXTRACTOR` to the upstream `controller_work` source root and `GVQCC`
to the prior repository checkout. Set `E4` to the pinned KMB. The branch
profiler is built from `$GVQCC/score5_dqi_width_branch.cpp`. In this directory
with the matching KickMix installed:

```sh
g++ -std=c++17 -O3 "$GVQCC/score5_dqi_width_branch.cpp" -o branch_lifetimes
./branch_lifetimes "$E4" branch_lifetimes.tsv > branch_lifetimes.json
python census.py "$E4" branch_lifetimes.tsv census.json --prior-code "$GVQCC" --dqi-source "$EXTRACTOR"
python split_crt.py --source "$EXTRACTOR" --out crt_native_last --degree 34 --node 0 --shots 1024
python bind_crt.py "$E4" crt_native_last crt_e4_bind.json --prior-code "$GVQCC" --output-kmb e4_crt_last_intermediate.kmb
./branch_lifetimes e4_crt_last_intermediate.kmb crt_branch_lifetimes.tsv > crt_branch_lifetimes.json
python crt_width_coverage.py . crt_width_coverage.json
```

`retire_f_loop.py` is a separate component study that retires an idle witness
from the raw-window F pass. It passed native tests but was not used in the CRT
splice.
