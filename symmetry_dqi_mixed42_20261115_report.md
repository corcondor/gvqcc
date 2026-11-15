# New GF4 mixed-place starts for the DQI GF12 multiplication tensor

## Outcome

Twenty exact 42-product decompositions were constructed from a different
interpolation family and searched for a 41-product result. **The best stayed
at 42; no new production circuit was generated.** This is a bounded search
result, not an optimality proof.

The target is precisely GF(2^12) multiplication modulo `0x1053`, the kernel
already matched at 3,823 places in DQI821. The input/output coordinates are
the original twelve-bit polynomial coordinates. Arbitrary target XOR is the
intended circuit contract; no candidate is allowed to change that contract.

## Why this was not the earlier experiment again

The installed 42-product construction uses a degree-four tower over GF8,
seven evaluation points and six binary products per point: `7*6=42`.
Earlier Polytof searches began with that family.

Here GF4096 is represented as a degree-six extension over GF4. Product
polynomials have degree at most ten, so eleven GF4 interpolation coordinates
are required. The new construction uses:

- All four finite GF4 points and the point at infinity: five coordinates,
  each requiring three binary products.
- Three distinct degree-two places over GF4: six coordinates, each place
  requiring nine binary products through GF16 multiplication.

The cost is `5*3 + 3*9 = 42`. There are six degree-two places; choosing three
gives twenty constructions. A 22-by-22 binary evaluation matrix is inverted
to recover all eleven GF4 coefficients, then evaluated in the original
GF4096 representation. The scalar kernel used at degree-two places is the
existing source's exactly checked nine-product GF16 multiplication.

The concrete field parameters are:

| Parameter | Value |
|---|---:|
| GF4096 modulus | `0x1053` |
| GF16 modulus | `0x13` |
| GF4 generator inside GF4096 | 70 |
| GF4 generator inside GF16 | 6 |
| Degree-six tower generator | 2 |
| GF16 Frobenius pairs outside GF4 | `(2,3), (4,5), (8,15), (9,14), (10,12), (11,13)` |

Every construction has 42 nonzero factor triples and was independently
checked on all 144 bit-basis pairs against integer polynomial multiplication.
Because each map is bilinear, these checks establish equality on all field
element pairs, not just a random sample.

There is a simple invariant demonstrating that the new starting family is
different. Among its 42 distinct first-axis binary linear forms, count the
unordered triples satisfying `u XOR v = w`. The installed GF8 construction
has **28**, whereas every new GF4 construction has **23**. An invertible
linear change of coordinates preserves this count. Consequently, these are
not just the installed factor sets in a different field basis.

In contrast, applying only common Frobenius/scalar autotopies to an existing
factorization would preserve its flip graph up to coordinate relabeling and
was not treated as a new experiment.

## Search budget and exact checks

PGL2(GF4) has 60 actions on the six degree-two places; its action on their
three-element subsets has two ten-element orbits. This is a classification
of the **evaluation-site sets**. Equivalence of all complete decompositions
after the fixed GF4096 quotient/output map is included is not asserted.
For that reason, all twenty starts were eventually searched.

| Initial starts | Paths per start | Steps per path | Maximum rank growth | Best |
|---|---:|---:|---:|---:|
| Two site-orbit representatives (records 0 and 2) | 128 | 1,000,000 | +8, reaching 50 | 42 |
| Other eighteen starts | 8 | 1,000,000 | +12, reaching 54 | 42 |

The first seeds were `202611150001` and `202611150002`. The remaining
record `n` used seed `202611151000+n`. The driver's consecutive path seeds,
burst interval 1,000, reduction interval 1,000, complete rank histograms and
best terms are recorded in the result JSONs.

Total measured work:

- 400 independent paths and 400,000,000 loop steps.
- **398,674,763 successful flips** and **14,962,890 successful plus moves**.
- **105.73 seconds** inside the search drivers, below the requested three
  minutes of CPU search time.
- 60,480 full-table coefficient checks across path endpoints and driver-best
  results, plus a separate Python oracle check of all 144 coefficients of
  each of the twenty reported best tensors.

The drivers used the pinned, unmodified Polytof BASE primitives already
documented in `theory_bilinear_report.md`. Only the initial decomposition
family and the explicitly recorded schedules changed. No Kaggle verifier,
scoring seed, competition file, or existing submission worker was altered.

## Reproduction and remaining scope

Generate the constructions with:

```sh
python symmetry_dqi_mixed42_20261115.py
```

Compile `theory_bilinear_depth.cpp` with the existing pinned Polytof source
as described in `theory_bilinear_report.md`, then run into fresh directories:

```sh
python symmetry_dqi_mixed42_20261115_search.py --driver /absolute/path/polytof-depth --output-dir /tmp/mixed42-deep
python symmetry_dqi_mixed42_20261115_search.py --driver /absolute/path/polytof-depth --breadth --output-dir /tmp/mixed42-breadth
```

The stored input JSON contains every factor triple, field parameter, input
hash, line-count invariant and site-configuration orbit. The two aggregate
result JSONs contain all twenty final tensors and all subprocess arguments;
the individual `orbit*.json` files and generated text inputs are redundant.

This experiment does not rule out a 41-product factorization, an initial
family with different geometric or jet evaluations, a successful longer
walk, or a measurement-aware nonlinear synthesis of a larger circuit map.
It does rule out describing these completed runs as a measured gate or score
improvement. The new practical result is a fully checked initial family
outside the installed factor-set basis orbit, now available for a future
stronger optimizer.
