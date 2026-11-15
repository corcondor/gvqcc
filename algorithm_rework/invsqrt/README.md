# Shorter arithmetic for direct inverse-square-root phase

This experiment changes the arithmetic rather than rewriting gates in the accepted tape. Normalize integer x exactly by a left shift, split the normalized mantissa into eight prefix bits and thirteen residual bits, and use an integer quadratic fit. Load the intercept and slope by prefix and by exponent parity. A curvature coefficient is shared by each eight adjacent prefix bins. The exponent is split into parity and half-exponent, so the coefficients already include the parity factor 1/sqrt(2) and only a binary scaling remains.

The existing accepted tape uses integer square root and division. This fit bypasses those operations, using a truncated slope product plus a narrow residual-square correction and a table-dependent intercept. The new computation has 512 table entries for intercept/slope including both exponent parities, and 64 curvature entries.

For the slope multiplier, let a be the unsigned 18-bit coefficient, b the 13-bit residual, and cut=12. Compute

    P_cut(a,b) = sum { a_i b_j 2^(i+j) : i+j >= cut }

and round at the designed fixed-point position. The first 12 diagonals in the 18×13 multiplication contain 78 products. In the native compiler these products are never formed, nor are their associated carry bits. All resulting binary words below column cut are zero, so the output of the component is represented as P_cut/2^cut. Refit the intercept in each bin to center the interval of possible total approximation errors.

## Measured results

- Mathematical fixed-point phase pipeline. All 3,133,452 admissible x pass the integer-rounded target/tolerance from the official verifier. Worst error is 0.73457463335 of permitted error and the minimum absolute margin is 1.06082087017e−11 turns.
- Native multiplier comparison, both using the same public measurement-carry adder backend.

| Slope multiplier | Partial-product Toffolis | Total Toffoli-like | Peak fixture Q | Operations |
|---|---:|---:|---:|---:|
| All diagonals | 234 | 468 | 97 | 2938 |
| First 12 diagonals omitted | 156 | 312 | 85 | 1924 |

On the actual derived slope/residual pair for every legal x, both serialized/reloaded KMB fixtures returned the intended product and restored both inputs and all scratch. The native phase check reported zero failures for the fixed simulator seed 42571. Each temporary AND for a product row is uncomputed by HMR with its corresponding CZ phase correction; row and carry auxiliaries are cleared before reuse.

The comparison is of arithmetic components from the new design. Numeric whole-pipeline feasibility and native multiplier correctness are separate results. The multiplier fixture by itself is still wider than the accepted full invsqrt circuit (46 Q). Its width includes separately registered multiplier inputs, output, row buffers and carries. The lookup, normalization, residual square, phase application and inverse cleanup are not integrated into a competitive whole circuit. There is no new submission or new competition score.

## Reproduce

Use system Python with NumPy to generate the coefficient table and check the full mathematical domain:

```sh
python shared_curvature.py --output shared_curvature.json
python truncated_product.py --output truncated_product.json
```

Use Python with NumPy and Kickmix for KMB generation and all-pair validation. Public backend source is from the Syed generator, directory `src/work/c10/narrow/checkpoint002/cleanroom/baseline_stage97` (applies its `engine/fusion/arithmetic.py` measurement-carry adder, Apache 2.0).

```sh
python multiplier_fixture.py --screen truncated_product.json --out native --source "$BACKEND_ROOT"
```

### Pins and scope

- Tested input domain is precisely `1 <= x <= 3,133,452`. Two multiplier fixture simulations each used one native sample at every derived (slope, residual) pair, split into batches of up to 65,536 with fixed per-batch seed 42571. The output is checked against the independently computed integer product with the intended diagonal rule.
- In the mathematical screen the official fixed-point reference is reproduced with `root = isqrt((1 << 130)//x)`, target `((root+1)>>1) mod 2^64` and tolerance `root>>25`. Predicted phases and signed differences are computed as exact integers modulo one turn; float64 is used only for choosing coefficients and reporting ratios. Verifier source SHA-256 `ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a`.
- Backend arithmetic SHA-256 `154621ee98dd8139eab601d5d794be881a5ebf38ebe1c542cf69b8fb97ee1453`, compiler SHA-256 `3980ca204863364f75e8d52b2e52a2515764da5dd5915aee7f347d7d325b06bb`.
- Native full-product KMB SHA-256 `62ae7abf72309efc5ee788efb82e6366bab33fe1c52e4bb0030a8a52c8c9c07a`; native narrowed-product KMB SHA-256 `5125f9f964614644dcac4d559f217a333423397747bcc0310269d94edf314cbb`.
