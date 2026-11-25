import Std.Tactic
namespace GVQCC.V41
def X := Bool.xor

theorem piecewise_affine (a b l00 l01 l1 : Bool) :
    (if a then l1 else if b then l01 else l00) =
      X l00 (X (a && X l00 l1) ((!a) && b && X l00 l01)) := by
  cases a <;> cases b <;> cases l00 <;> cases l01 <;> cases l1 <;> decide

-- r can be nonzero, but its old value is irrelevant to the target
-- precisely on the care set c. Both data outputs are restored.
theorem conditional_clean (a b c r t : Bool) (h : (c && r) = false) :
    (X (X r (a && b)) (a && b), X t (c && X r (a && b))) =
      (r, X t (a && b && c)) := by
  cases a <;> cases b <;> cases c <;> cases r <;> cases t <;> simp_all [X]

theorem dirty_four (a b c r t : Bool) :
    (X (X r (a && b)) (a && b), X (X t (c && X r (a && b))) (c && r)) =
      (r, X t (a && b && c)) := by
  cases a <;> cases b <;> cases c <;> cases r <;> cases t <;> decide

-- Same-carrier fusion, conditional on no uncompensated intermediate reads.
theorem carry_fusion (r a b c : Bool) :
    X (X r (a && b)) (a && c) = X r (a && X b c) := by
  cases r <;> cases a <;> cases b <;> cases c <;> decide

theorem phase_transport (g r h t : Bool) :
    X (g && X r h && t) (g && r && t) = (g && h && t) := by
  cases g <;> cases r <;> cases h <;> cases t <;> decide

-- Actual [10115,10145) projected cubic decoder.
-- a=q0, b=q21, l=the extracted affine parity, r=q29.
-- Reachable premise b*r=0 verified by independent exact BDD prefix replay.
theorem native10115 (a b l r t : Bool) (h : (b && r) = false) :
    (X (X r (a && l)) (a && l), X t (b && X r (a && l))) =
    (r, X t (a && b && l)) := by
  cases a <;> cases b <;> cases l <;> cases r <;> cases t <;> simp_all [X]

theorem budget_receipt :
    3211 - 29 - 14 = 3168 ∧ 23127 + 96 = 23223 ∧
    41967 + 61 = 42028 := by decide
end GVQCC.V41
