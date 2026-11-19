# Round 48 DQI: local shared-output and multistage experiments

Input: the DQI member of `gvqcc_round48_hierarchy16_evaluation_18files_20261119.zip`,
SHA256 `669edf233ee8f64f3f2f5e29701256c89207ccb244d1313c2c4fec092649458e`.
This is a local research candidate, not the user's Kaggle 28.319 submission. It
has known whole-circuit regressions. Results do not claim a replacement circuit,
a repaired regression, any Toffoli saving, or a score update.

Requires Python 3 with NumPy. Run from the source directory:

    unzip -p gvqcc_round48_hierarchy16_evaluation_18files_20261119.zip dqi.kmb > round48.kmb
    sha256sum round48.kmb
    python3 relation_rank_search.py round48.kmb --self-test
    python3 relation_rank_search.py round48.kmb > rank_relation_receipt.json
    python3 operand_span_probe.py round48.kmb > operand_span_receipt.json
    python3 nonlinear_degree_probe.py round48.kmb > nonlinear_degree_receipt.json

All results treat the physical window-entry wires as independent Boolean variables.
Lookups are by the existing 42-CCX motif's canonical operand pattern, require the
expected 1,293-instruction span on each side, and admit only CX/CCX with no
measurements in the total window. Indices are zero-based.

## Shared outputs

45 rank-12 windows have 42 output directions, each used by exactly two product
terms. Each window's four operand subspaces have dimension 12; the two kernels'
24-dimensional input coordinate spaces have intersection dimension zero on this
cut. Thus these pairs do not have a common operand even after changing its basis.
This is a statement about this cut, not proof that reachable input states do
not satisfy extra constraints induced by the enclosing algorithm.

Quadratic maps were represented by alternating matrices modulo linear terms
(the linear terms can be restored with XOR at function level). For a given fixed
exit direction the minimum product count for this one scalar quadratic part is
half its rank. Reassign an alternating rank-2 atom to each direction of a
three- or four-direction XOR relation, which preserves the vector map's
quadratic part exactly. The implementation enumerates all two-dimensional
planes within any existing direction's row space. Across these windows there
were 49 relations and 1,470 candidate atoms in each window; the resulting bound
stayed 84. This is not a claim of 84-product optimality.

## Genuine multistage cubic windows

Transitively expand CCXs in exact Boolean ANF, using set XOR and monomial
products with idempotent variables. There are 18 windows with cubic terms
surviving at the exit; every one of the 42 second-kernel controls is a
degree-2/degree-1 pair. No single layer of products of input-affine forms can
compute the entire cut-local cubic map. The 18 is for the Round 48 hash above,
not the 10 structural pairs already reported for a different DQI file.

Before adopting a replacement, restore linear basis changes and ancillas,
check each caller's zero/dirty and HMR phase contracts, and verify on the same
integrated circuit hash against fixed regressions and both official panels.

## 28.5 への規模感

[別の添付回路の監査](../../../2026-11-20_dqi_42_kernel_repetition_audit.md)で見つかった4,053核を例にとると、重複なしの2核融合は最大2,026組。各組で3 CCXを消しても静的6,078個なので、[Round 48の費用感度](../../../2026-11-20_cross_session_synthesis.md#g-目標285に対する費用感度実測ではなく数式)が示す平均約6,818個に届かない。4個/組でも、実際に適用できる組数・実行分岐・修復費用次第。4,053核はこのRound 48実験とは別ハッシュの数なので、移植時は数え直す。少数の共同合成窓は検証用、共通核への広い適用や幅削減は並行課題とする。
