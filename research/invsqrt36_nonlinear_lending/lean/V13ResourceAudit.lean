import Std.Tactic
namespace V13ResourceAudit
-- Units are sixteenths of an expected paid gate, from actual native BDD replay.
theorem cost_partition : 24435 + 1720 + 620 = (26775 : Nat) := by decide
theorem wide_partition : 24819 + 592 + 1676 = (27087 : Nat) := by decide
theorem direct_only_insufficient : 24435 + 620 > (23233 : Nat) := by decide
theorem unchanged_charts_insufficient : 24435 > (23233 : Nat) := by decide
-- 23233/16 is a conservative upper bound on the conditional break-even 1452.05390236.
-- Algebraic hypothesis only, not a compiled candidate: for odd a,
-- the newest digit is stored in the parity of the product accumulator.
theorem digit_recovery (a p : Int) (d : Bool) (ha : a % 2 = 1) :
    (2 * p + (if d then a else 0)) % 2 = (if d then 1 else 0) := by
  cases d <;> simp <;> omega
theorem product_recovery (a p : Int) (d : Bool) :
    (2 * p + (if d then a else 0) - (if d then a else 0)) / 2 = p := by
  cases d <;> simp <;> omega
end V13ResourceAudit
