# Chemistry rebatching: independent contract and cost audit

## Decision thresholds

For the accepted score8 coefficients and exact actual angle table, **J=4 requires 19 circuits**, and lowers the scored qubit count from **427 to 419**. It improves the current portfolio if the aggregate loader cost per pass **A < 4170.544152744630**. For an unconditional integer-cost family the maximum is **4170**. Reaching portfolio score28 through this task alone requires **A <= 3643.171142987305**, or **3643** for integer cost.

The older threshold4173 used score6's 14728 total Toffoli. Its precise same-lambda threshold is 4173.601431980907. The accepted score8 circuit already uses14722, so that old threshold is no longer the correct improvement gate.

These are conditional resource targets, not emitted circuits or new verified scores. Other tasks, coefficients, brot8 and the actual decoded angle words are fixed. No full verifier, circuit mutation or submission was performed by this audit.

| J | Files | Final padding words | Scored Q | Maximum angle workspace | Improve: A strictly below | Integer maximum | Reach28: A at most | Integer maximum |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 75 | 0 | 395 | 109 | 4626.334177 | 4626 | 4066.918250 | 4066 |
| 2 | 38 | 1 | 403 | 101 | 4468.372208 | 4468 | 3920.061312 | 3920 |
| 3 | 25 | 0 | 411 | 93 | 4316.559611 | 4316 | 3778.921433 | 3778 |
| 4 | 19 | 1 | 419 | 85 | 4170.544153 | 4170 | 3643.171143 | 3643 |
| 5 | 15 | 0 | 427 | 77 | 4030.000000 | 4029 | 3512.507515 | 3512 |
| 6 | 13 | 3 | 435 | 69 | 3894.625287 | 3894 | 3386.649906 | 3386 |
| 7 | 11 | 2 | 443 | 61 | 3764.139955 | 3764 | 3265.337943 | 3265 |
| 8 | 10 | 5 | 451 | 53 | 3638.283814 | 3638 | 3148.329732 | 3148 |

The official scalar helper gives state preparation plus Givens cost6662, persistent preparation qubits84 and shared workspace303. Every angle circuit has11 selection qubits and8J word qubits, with a separate hard cap128. Thus

\[
T_{total}=6662+2A,\qquad Q_{total}=84+8J+\max(303,Q_{angle}-11-8J)=387+8J.
\]

The scored chemistry cost is lambda_eff times these two factors. Here lambda_eff=46.909667503120325; current chemistry cost=294887961.3668603; current portfolio score=27.32784222155277. The target28 chemistry cost is 274156769.4201537, a factor 0.929698072954170 of current cost. A is half of the simulator's actual forward-plus-reverse mean, not necessarily the static gate count when measurements control Toffoli execution.

## What the family must load

Each circuit uses identical `selection` and `word_0` through `word_(J-1)` quantum registers, with identical physical IDs. Selection is exactly11 qubits. The number of circuits is exactly ceil(75/J). The words observed after circuitk are concatenated in file order as columns kJ through kJ+J-1. There is no independent angle-index map or variable final J.

For J4 the last file has three valid words and one zero padding word. That fourth register remains present and charged. Its final transition must clear the prior batch's fourth word; simply omitting it is incorrect. All final padding must be zero on every valid address.

The directory loader accepts contiguous `angle_k_0.kmb` through `angle_k_18.kmb` (or consistently kmx). The Python API also accepts an ordered list of arbitrary paths or Circuit objects. This only changes the source of the ordered family: exact circuit count, fixed register layout and positional output order still apply. Extra helper/identity files do not provide a free prefix stage.

After **every file**, the verifier checks zero quantum workspace, preserved selection and zero phase. It then clears simulator state and restores **only selection and word values**. Neither quantum scratch nor classical measurement bits can carry a prefix into the next file. Prefix sharing is possible inside one circuit, across its internal subcomputations, followed by correct cleanup.

The303-qubit temporary cost floor does not override the128-qubit angle-circuit cap. J4 has at most85 angle workspace qubits, versus77 at J5. Unused or named extra qubits still count through `Circuit.num_qubits`; the11-qubit selection width cannot be enlarged to hide them.

## Existing v27 structure and reusable controls

All15 accepted loaders were read without modification; their static Toffoli counts sum to4030. For k1 through k14 the exact common high-address prefix has **68 CCX**, and six further CCX complete the low-address features. The prefix total is74. Its HMR and conditioned-CZ cleanup has no extra CCX. The first circuit has initialization interleaved with nonlinear control updates and needs separate treatment; the old simple output-window extractor does not apply to it unchanged.

The actual recovered1220×75 angle table satisfies, for every address and every column,

\[
\mathrm{bit}_6(w_c)\oplus\mathrm{bit}_7(w_c)=a_p a_q,
\]

where the pairs repeat with column modulo5 as (0,1), (0,2), (1,2), (0,3), (1,3). A CX exposes this known tag at no Toffoli cost **on the appropriate reachable input batch**. At J5 the same slot has the same tag in each batch. At J4 the four present tags rotate; incoming and outgoing tag layouts differ, and the last padded slot is zero. At k0 all incoming words are zero, so no such preloaded tags exist.

The JSON also computes the exact intersection of each batch's word/address linear span with functions of the low four address bits. This records which of the five tags really are available without a nonlinear gate. It does not assume that a changing tag remains available across a circuit boundary.

Completing the full low-four-bit monomial basis from four distinct preloaded tags naturally takes seven missing products, rather than the six used with five tags. This is a basis-construction estimate, **not a complete J4 loader cost**: changing tags, word-output synthesis, cleanup and the reverse path still need a correct construction. The smaller word bank does free eight physical qubits under the cap, which can help that construction.

The output accumulation blocks mix many target bits by CX gates. Deleting all gates aimed at unwanted physical output qubits is not a valid way to project onto a smaller word subset. Each CCX's complete output direction must be propagated through the suffix. In addition, the new transition function is old-new-batch XOR new-new-batch; it is not generally a projection of one old J5 transition.

The accepted NPZ declaration differs from the actual decoded table in473 entries. Rebatch synthesis must use the hash-pinned recovered words, not silently replace them with the declared `angle_words` array, if it intends to retain the accepted chemistry metrics.

## Reordering and the exact oracle claim

Noncontiguous old angles can only be grouped by changing their order in the decoded table and correspondingly changing/re-encoding `tree_edges`. The verifier requires a rooted tree in parent-before-child order, but that condition alone does not preserve the old vector. Ordered Givens rotations sharing a vertex generally do not commute. Swapping disjoint rotations preserves the vector exactly; any more general permutation needs a separate equivalence or physics check.

The written circuit contract specifies an arbitrary-target XOR oracle. The executable verifier checks its forward and reverse reachable batches. A proof that word6 XOR word7 equals an address product on those batches is not a proof for arbitrary targetz. Candidate reviews must state whether they establish the reachable isometry, the arbitrary-target XOR extension, or both. This distinction already applies to the inherited tag-based public loaders and should not be hidden by rebatching.

X/CX/CZ and classical logic are not charged as Toffoli-like operations; HMR/R are available with correct phase and cleanup. CCX/CCZ/CSWAP contribute actual executed counts. Z_POW is explicitly rejected. Reaction depth and instruction count are reported but do not multiply this task's scalar score.

## Evidence and reproduction

`score9_rebatch_contract.json` pins the official source files, accepted scorecards, NPZ, recovered actual words and all15 circuit files, and records function source locations. `score9_rebatch_contract.py` calls only the official scalar heuristic helper and reads circuits/arrays; it does not run `verify` or mutate a submission. Re-run it with the existing Kickmix Python environment to reproduce both the JSON and this report.
