import Std
import Lean.Elab.Tactic.Omega

namespace V19WidthBudget
-- Expected paid-gate units are sixteenths in the two archived circuits.
-- Rotation-cost constant is the frozen decimal model, not an official verifier.
def rotationScale : Nat := 100000000000000
def rotationScaled : Nat := 24037798500105055
def scaledCost (q e16 : Nat) : Nat := q * (e16 * rotationScale + 16 * rotationScaled)

theorem resource_partition : 22581 = 6910 + 15671 := by decide
theorem live_direct_partition : 6910 = 2440 + 4470 := by decide
theorem last_allowed_grid_cost : scaledCost 36 23232 < scaledCost 37 22501 := by decide
theorem first_rejected_grid_cost : scaledCost 37 22501 < scaledCost 36 23233 := by decide
theorem grid_budget : 23232 - 22581 = 651 := by decide
-- Conditional: no compensating savings and every counted lifetime adds >= 1/2 gate.
theorem half_gate_epoch_limit (n extra16 : Nat)
    (h : 8*n <= extra16) (budget : extra16 <= 651) : n <= 81 := by omega
theorem full_per_epoch_half_gate_over_budget : 651 < 8 * 306 := by decide
end V19WidthBudget
