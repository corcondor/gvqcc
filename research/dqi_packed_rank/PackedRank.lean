import Std
namespace PackedRank

/-- Relative XOR updates telescope along any coherent path. -/
def debt (a : Bool) : List Bool → Bool
  | [] => false
  | b :: bs => (a ^^ b) ^^ debt b bs

def endpoint (a : Bool) : List Bool → Bool
  | [] => a
  | b :: bs => endpoint b bs

theorem debt_telescope (a : Bool) (xs : List Bool) :
    debt a xs = (a ^^ endpoint a xs) := by
  induction xs generalizing a with
  | nil => cases a <;> decide
  | cons b bs ih =>
    simp only [debt, endpoint, ih b]
    cases a <;> cases b <;> cases endpoint b bs <;> decide

/-- A product gate that is coherently disabled has identity action. -/
def eff (on a : Bool) := true ^^ (on && (a ^^ true))
theorem effective_pivot (a : Bool) : eff false a = true := by
  cases a <;> decide
theorem effective_pivot_active (a : Bool) : eff true a = a := by
  cases a <;> decide

theorem masked_shear_involution (act x y z : Bool) :
    ((z ^^ (act && x && y)) ^^ (act && x && y)) = z := by
  cases act <;> cases x <;> cases y <;> cases z <;> decide

theorem hmr_phase_repay (m act x y : Bool) :
    ((m && act && x && y) ^^ (m && act && x && y)) = false := by
  cases m <;> cases act <;> cases x <;> cases y <;> decide

theorem packed_capacity (v q : Nat) (h : v + 1 ≤ q) :
    2 * (v + 1) + 2 * (q - (v + 1)) = 2*q := by omega

#print axioms debt_telescope
#print axioms effective_pivot
#print axioms effective_pivot_active
#print axioms masked_shear_involution
#print axioms hmr_phase_repay
#print axioms packed_capacity
end PackedRank
