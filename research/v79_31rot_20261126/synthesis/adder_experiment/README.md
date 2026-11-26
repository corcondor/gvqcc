# Coherent first-Horner connector: exact carry decomposition

This is a complete native **first-Horner chart roundtrip**, using the repaired V61 B35 coefficient model. It preserves the full coherent signed 21-bit word and its rounding residue. It is **not** a complete inverse-square-root oracle, and it does **not** establish the original V55 B34 / 31-rotation port.

## Results

| Connector method | Q | CCX in complete first-stage roundtrip | Instructions | Forward connector CCX |
|---|---:|---:|---:|---:|
| Address NAF, original multi-controls | 36 | 39,527 | 46,260 | 19,586 |
| Shared signed digits + exact commute cancellation | 36 | 19,939 | 25,880 | 9,792 |
| Borrowed-bit linear incrementer (port31 agent) | 36 | 9,043 | 21,236 | 4,344 |
| Split low/high words + clean carry pebbling | 36 | 2,699 | 15,200 | 1,172 |
| Clean address lookup + flag routing | 36 | 1,995 | 14,352 | 820 |
| **Exact reachable-carry pruning** | **36** | **1,239** | **9,898** | **442** |

The final candidate reduces the connector's forward CCX count by **89.825%** versus the linear incrementer. The complete first-stage circuit has the inherited 10 classically guarded CCZ gates, so its expected paid count is **1,244**, distinct from the unconditional CCX count of 1,239. It contains zero rotations because the output is a coherent word for the next arithmetic stage.

Final file:

`coherent_first_horner_split_carry_reachable_Q36_PARTIAL.kmb`

SHA256:

`073977d70d70a602b7afc7f18a36fb2e50acea5f20d787849b0b621c843ba684`

## Verification

Every new candidate passed serialized native replay over all **3,133,452 legal inputs**, with independent HMR phase coefficients, the physical 21-bit word at the middle snapshot, correct decoding using only that word and the retained address, retained rounding residue, and complete restoration of input and workspace.

The final decoded first-stage integer word has SHA256:

`1c05552f7be2b134e85c73d91903cb038c68043e8e76d70984ff89a900462408`

Its signed encoded range is **−638,358 through 4,095**. This requires 21 signed bits in this encoding; 20 signed bits would not suffice. Official KickMix binary parser results, where present, are recorded separately in the receipt. A parser check is not the full inverse-square-root verifier.

## Exact construction

At the donor boundary, let

- `P = odd(address) * T`, with `0 <= T <= 4095`;
- `K(address)` be the first-Horner constant including the shift/rounding chart;
- `A = P + K(address)` be the signed 21-bit output;
- `K = K_low + 2^16 K_high`, with `0 <= K_low < 2^16`.

The donor's 16 product bits occupy `q5..q16,q27..q30`. Five high-word wires `q26,q31..q34` are initially zero. The address remains in `q17..q21`; `q35` is a flag wire.

### 1. Low-word addition while the high word remains clean

Compute

`S = (P + K_low) mod 2^16`

without writing the high word. All five high-word wires remain available as genuinely clean carry workspace.

A shortest-path pebble scheduler generates conditional increments. A node `C_j` holds the exact carry

`C_j = flag AND x_0 AND ... AND x_(j-1)`.

Computing a node costs one CCX. When its predecessor and unchanged source bit are present, HMR plus the corresponding guarded CZ erases it with zero additional CCX. A sum bit is toggled only after every stored carry depending on it has been erased. This permits reuse of five carry wires without dropping any arithmetic information or measurement phase.

The signed increments for each address commute as modular additions. Equal flag masks are grouped, and the flags are transported by their exact XOR differences. Address cubes use the clean high-word workspace and measurement uncomputation instead of the older dirty multi-control expansion. The final low-word addition costs **354 CCX**.

### 2. Carry from the low sum

The high-word carry is exactly

`c = [S < K_low]`.

A constant comparison is an XOR of matching-prefix predicates at changes in the constant's bit string. A second pebble scheduler produces these predicates with four clean temporary lines, while `q26` accumulates the carry. The unrestricted version costs 385 CCX after clean lookup.

The actual reachable product range makes almost all comparisons unnecessary. Since

`0 <= P <= odd(address)*4095 < 65536`,

carry can occur only if

`odd(address)*4095 >= 65536 - K_low(address)`.

The exact 24-row integer certificate shows this is possible **only at coefficient-table index a=0**. Here the zero-based table index a is distinct from the retained five-bit physical address a+8, which is 8 for this row. At every other table index the carry is identically zero. The single remaining comparator costs **44 CCX**, including address flag handling. No samples or numerical tolerances are used for this pruning.

### 3. High-word extension

The high word is `K_high + c`. At the only address that can carry, `K_high = -10`, which is even. Therefore its increment changes only its least significant bit. For all other addresses, `c=0`.

Consequently:

- high bit 0 is `K_high_bit0 XOR c`;
- all higher high bits are exactly the corresponding address-dependent constant bits.

This removes all higher carry-propagation gates. The high extension costs **44 CCX** for address lookup and writes.

The forward connector therefore costs

`354 + 44 + 44 = 442 CCX`.

Its inverse is independently synthesized: undo the high constants, recompute the same comparison to clear the carry bit, then perform the negative low-word addition. HMR-containing instruction lists are never reversed as though they were ordinary unitary gates.

## Reproduction

The directory layout expects `port31/` beside `synthesis/`, as in the prepared repository package. Only the existing native donors and Python dependencies are used.

```sh
python synthesis/adder_experiment/split_carry.py
python synthesis/adder_experiment/clean_lookup.py
python synthesis/adder_experiment/reachable_carry.py
```

Each command emits its own KMB, independent verification receipt, and console results. The final command also writes `reachable_carry_integer_certificate.json`, containing the full product bounds, carry thresholds, and high-word increments for all 24 addresses.

The successful arithmetic connection does not bridge the differing V55 B34 and V61 B35 specifications. The original 31-rotation claim still requires a complete native chain for the exact B34 coefficients and all subsequent Horner stages; the accompanying port31 audit documents that remaining gap.
