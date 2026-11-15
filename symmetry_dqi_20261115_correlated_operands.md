# DQI correlated-operand audit: existing specializations and one full-domain check

## Result and scope

A bounded source audit found no immediate replacement of a general quantum
field multiplier by a square, a constant linear map, or a norm. The inspected
Syed source already uses linear squaring and tower-field norm constructions.
This is not an optimality claim or a complete semantic audit of the submitted
binary. The source tree includes experimental implementations that need not
all be active in any particular submitted circuit.

The AST scan examined **269 quantum product calls** and found **zero calls with
syntactically identical left and right operand expressions**. This excludes
only an explicit `multiply(a,a)` pattern within the named APIs and scan scope;
it does not establish that distinct aliases cannot contain the same value.

The source root is
`official_sources/Syed_v12/source/dqi_source/src/controller_work` beneath
`/workspace/scratch/7f542e06b7cf`. File hashes and exact scope are recorded in
`symmetry_dqi_20261115_correlated_operands.json`.

## Concrete inspected constructions

1. **Linear squaring.** In
   `night_c27/arithmetic/phase_inverse12.py`, `fixed_inverse_trace12` constructs
   the columns of the four-bit squaring map and applies them with `xor_linear`.
   It does not emit a general field multiplication for each square.

2. **Quadratic-extension norm.** In
   `work/round2/milestone152/source/tower_inverse.py`, `init_norm` constructs
   `a^2 + a*b + delta*b^2` using one `xor_product(a,b)` and two linear maps.
   `erase_norm` applies the corresponding measurement-phase correction.
   `night_c27/arithmetic/gf24_arithmetic.py` calls this construction in its
   deferred and closed inverse routines. The useful conjugation/norm structure
   is already represented explicitly.

3. **Nested inverse.** In
   `night_schedule/modular_quadratic_direct.py`,
   `inverse_twelve_deferred` converts the twelve-bit word into a quadratic
   tower, computes the six-bit norm inverse, and multiplies each source half
   by it. Its general products are not explicit same-operand squares.

4. **Chien constants.** The separate official
   `Inzainos/verifiers/dqi/dqi_reference_circuit.py` builds fixed
   `step_multipliers` and calls `builder.gf2_imul(step, ...)`. These constants
   are routed through the constant-multiplication API, not through a pair of
   arbitrary quantum field inputs. This reference source is not asserted to
   be byte-identical to the optimized submitted circuit.

## A superficially correlated product still has the complete operand domain

`fixed_inverse_trace12` contains

```python
accumulate_product(builder, a, B, C, Base.gf16_kernel())
```

Here `B` includes `a^2`, as well as a function of the independent four-bit words
`b,c`. To check whether that relationship reduces the multiplier's reachable
input domain, the audit independently evaluated `JOINT_GATES` and
`JOINT_OUTPUTS` from `inverse_phase27.py`.

The image of `joint_B(b,c) XOR b^2 XOR c^2` is all sixteen GF16 elements. Thus,
for each fixed `a`, the word `B` also ranges over all sixteen elements.
The explicit enumeration found **256 distinct `(a,B)` pairs out of 256**.
The presence of an `a^2` term therefore does not justify replacing this call
by a square or a constrained-operand multiplier. This domain observation
does not exclude optimization of the larger combined `a,b,c -> outputs`
network.

## Reproduction

Run the following AST check with ordinary Python. It only reads source files:

```python
from pathlib import Path
import ast

root = Path('/workspace/scratch/7f542e06b7cf/official_sources/Syed_v12/source/dqi_source/src/controller_work')
names = {'xor_product', 'accumulate_product', 'product',
         'ixor_gf2_mul', 'gf2_mul', 'init_gf2_mul'}
count, hits = 0, []
for path in root.rglob('*.py'):
    try:
        tree = ast.parse(path.read_text())
    except Exception:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = (node.func.attr if isinstance(node.func, ast.Attribute) else
                node.func.id if isinstance(node.func, ast.Name) else '')
        if name not in names:
            continue
        offset = 0 if name in {'ixor_gf2_mul', 'gf2_mul', 'init_gf2_mul'} else 1
        if len(node.args) < offset + 2:
            continue
        count += 1
        left, right = node.args[offset:offset+2]
        if ast.dump(left) == ast.dump(right):
            hits.append((str(path), node.lineno, ast.unparse(node)))
print(count, hits)  # Observed: 269, []
```

The finite-field check requires the existing KickMix environment:

```python
from pathlib import Path
import ast
import kickmix as km

path = Path('/workspace/scratch/7f542e06b7cf/official_sources/Syed_v12/source/dqi_source/src/controller_work/work/round2/milestone152/source/inverse_phase27.py')
constants = {}
for node in ast.parse(path.read_text()).body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in {'JOINT_GATES', 'JOINT_OUTPUTS'}:
                constants[target.id] = ast.literal_eval(node.value)
field = km.GF2Field(4)
image, pairs = set(), set()
for bc in range(256):
    products = [((bc & left).bit_count() & 1) * ((bc & right).bit_count() & 1)
                for left, right in constants['JOINT_GATES']]
    joint_B = sum((((bc & linear).bit_count() & 1) ^
                   (sum(products[j] for j in range(len(products)) if mask >> j & 1) & 1)) << out
                  for out, (linear, mask) in enumerate(constants['JOINT_OUTPUTS'][:4]))
    b, c = bc & 15, bc >> 4
    remainder = joint_B ^ field.mul(b,b) ^ field.mul(c,c)
    image.add(remainder)
    for a in range(16):
        pairs.add((a, remainder ^ field.mul(a,a)))
print(sorted(image), len(pairs))  # Observed: [0,...,15], 256
```

No circuit, source, submitted artifact, or remote state was modified by the
audit. This report records the completed read-only checks; no new gate saving
or score improvement follows from them.
