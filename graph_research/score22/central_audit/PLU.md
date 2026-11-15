# Adaptive PLU residue consume

## The 99-Toffoli accumulator

The installed GF24 tensor uses 99 Toffoli with three independent registers.
Each term consumes two parity controls and XORs its output direction into the
third register. With the proposed target/input alias, the entire XOR
accumulator would give `P ← (1 + D)P`. For the unit input `D=1`, it would
map every `P` to zero, while the desired multiplication is the identity.

Term-by-term aliasing also fails with the installed parity controls. There
are 52 noninvertible individual aliased updates and 4,616 dependencies from
a parity read to a conflicting update. The dependency graph is one strongly
connected component of all 99 terms. This tests the installed factors and
fixed parity controls. Other in-place algorithms can change those controls.

At the scalar CRT points, with `D,P` fixed, the degree-34 map from the old
`N` coefficients to the 34 scalar coordinates is invertible and has binary
rank 408. The actual `dqi_all` production prefix was also simulated for 1,024
stock-sampler syndrome/mask inputs. The 432 scalar-output plus old-`P` bits
have affine rank 433 including the constant. With the 24-bit `D` residue
included, the affine rank is 457. These real states exclude a fixed affine
dependency for borrowing space in those coordinates. Other nonlinear
encodings remain possible.

## Forward and reverse in-place decomposition

Write the field source as `u=a+bθ`, with `θ²=θ+δ`. The first chart uses
`a≠0`. The second chart swaps the two halves if `a=0`, then accounts for
the factor `θ` using a constant controlled linear map. For
`r=b/a`, use:

1. Add `δ r y` to `x`.
2. Multiply `y` by `1+r+δr²`.
3. Add `r x` to `y`.
4. Multiply each half by `a`.

The reverse order divides the target. The determinant encoding retains
one coordinate of the kernel of `r → r+δr²` so it can restore `r`.
GF12 inversions visit the factor in place and repay their measurement
phases with the relevant mask basis. The forward stores only the original
high-half target mask, padded with zero low-half bits, in the caller's
24-bit old-target mask ABI. The closed tester checks these exact debt
semantics and the phase from an inserted random output probe.

| Actual native circuit | Helper qubits | Static Toffoli | Shots per variant |
| --- | ---: | ---: | ---: |
| PLU residue forward | 14 | 694 | 8,192 |
| PLU residue closed pair | 14 | 1,547 | 8,192 |
| Original degree-34 CRT pair | 24 | 3,300 | 2,048 |
| PLU degree-34 CRT pair | 14 | 4,403 | 2,048 |

The pair supports both nonzero charts and the `source=target=0` extension.
The determinant and inverse phases use the same finite field as the
existing decoder. The degree-34 scalar steps allocate no temporary output
word.

## Exact binding to the current DQI tape

The tested intermediate binds the forward and matching return to
`dqi_phase_peak/dqi_all.kmb` (SHA-256 `9d97cda71833e8ae4776355b9c39d3b90fba6f778bf4e869345feff477892d1d`).
One earlier masked-phase splice falls inside the changed return and is
absorbed by it. Exact column matching confirms the remaining bytes around
both bound regions. The candidate keeps the 24 exported mask IDs and
checks next-use ownership for 496 retired classical bits.

| Fixed-order lifetime analysis | Previous | PLU pair |
| --- | ---: | ---: |
| Degree-34 forward peak | 889 | 879 |
| Degree-34 forward width-889 cuts | 373,046 | 0 |
| Degree-34 return peak | 889 | 889 |
| Degree-34 return width-889 cuts | 7,625 | 16,971 |
| Whole circuit peak | 889 | 889 |
| Whole circuit width-889 cuts | 8,607,724 | 8,244,161 |

The isolated return's 14-helper result does not establish an integrated
return width decrease. A 1,024-shot diagnostic observed the entire
return helper bank at zero at entry. A uniform clean-bank certificate
and a changed allocation at that seam are pending.

The unmodified DQI verifier passed 1,024 shots with zero value errors and
zero phase errors at `log2_delta=-12`. Mean charged operations increased
from 382,069.68 in the previous smoke run to 383,170.24. This intermediate
does not improve the whole score and is not intended for submission.

## Reproduction

Use the same `EXTRACTOR`, `GVQCC` and `E4` variables as in the central
audit README, plus the exact `dqi_all` tape, its `splice_all.json` overlay
receipt, and the stock DQI verifier:

```sh
python alias_99.py --source "$EXTRACTOR" --report alias_99.json
python plu_residue.py --source "$EXTRACTOR" --out plu_native
python plu_crt.py --source "$EXTRACTOR" --out plu_crt_native --degree 34 --node 0
python splice_plu_crt.py "$DQI_ALL" plu_crt_native plu_dqi_all_bind.json \
  --source-sha 9d97cda71833e8ae4776355b9c39d3b90fba6f778bf4e869345feff477892d1d \
  --prior-code "$GVQCC" --old-reference "$E4" --overlay-receipt "$OVERLAY" \
  --output-kmb plu_dqi_all_intermediate.kmb
python "$DQI_VERIFY" plu_dqi_all_intermediate.kmb --num-shots 1024 \
  --batch-size 256 --max-workers 4 --log2-delta -12 > plu_stock_smoke.json
```
