# GF(2^24) multiplication with a normalized source and one field-word buffer

The source is 1+rθ, θ²=θ+δ over GF(2¹²), and the target is x+yθ.
The low source half is initialized to the known word 1; it is restored
exactly on exit. Both the high source half r and target are otherwise
arbitrary.

For the prefix, compute d=r*y into a single 12-wire temporary. Then update
x'=x+δd and y'=y+d+r*(x'+δd). The second product uses the linear form
x'+δd=x directly inside the CCX controls. It never saves the old x or
allocates a second output word. HMR erases d and records its phase.
This prefix uses 84 Toffoli-like gates and 12 extra qubits. The generic
rank-99 product projected onto the same source chart uses 90 gates
and its original 24 extra qubits.

For the return, y'+r*x'=(1+r+δr²)*y. Write N=1+r+δr². Its computation
requires only an affine transform on r, since squaring in GF(2¹²) is
binary linear. The nonzero norm is formed in the known lower source half
and inverted there. The old norm is still an affine function of r, so its
measurement mask can be repaid, followed by restoring y with one scalar
product. After HMR-erasing 1/N the caller's low half is reused for N and
the inverse phase and old scaled-y phase are paid. Finally undo the affine
norm computation, set the lower source half back to 1, restore x with
δ*r*y, and pay the prefix's d measurement from restored r and y.

The control masks in the test are independently verified using a phase probe
between prefix and return. All 4096 distinct r appear in two deterministic
target assignments per r, at two independent fixed HMR seeds (16,384 shots
per listed circuit). Source, target, clean scratch, and phase all agree.
The value identities apply to every target; the simulation uses finite
target assignments.

| Paired circuit in the same chart | Extra qubits | Static Toffoli | All instructions |
|---|---:|---:|---:|
| Original source-family product and return | 24 | 459 | 48,560 |
| Original schedule specialized on both passes, including affine norm and projected conjugate product | 24 | 357 | 42,174 |
| Streaming prefix and one-bit norm-coordinate return | 12 | 369 | 31,714 |
| Streaming prefix and reciprocal norm in fixed source half | 12 | 303 | 30,501 |

The width comparison keeps the 48 caller qubits in all cases. The last row
uses the caller's known 12-bit source word as temporary storage. These resource
counts do not apply to a generic 24-bit source, and no call site in the
score11 decoder has been bound to this normalized domain. The experiment
does not run the full DQI verifier or establish a portfolio score change.

Use the compatible KickMix and NumPy environment and the existing Syed v12
controller_work source tree:

```sh
OPENBLAS_NUM_THREADS=1 python normalized_product.py \
  --work /path/to/controller_work --out reproduced
```

The generated circuits and report can be compared by their SHA-256 hashes
in result.json. The check of the specialized original schedule uses only
the explicit chart substitution in its product controls and affine norm
gates; the original provider is restored after each build.
