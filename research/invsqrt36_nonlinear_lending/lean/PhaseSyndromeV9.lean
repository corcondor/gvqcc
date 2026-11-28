import Std.Tactic.BVDecide

/-!
# V9 global sign-phase ledger and concrete affine cofactor updates

The generic algebra is universal. The eight concrete gate lists are conditional
on the reachable-state identities established separately by the exact BDD replay.
This is NOT a Lean theorem about the complete KMB parser or numerical oracle.
-/
namespace GVQCCV9

theorem phase_pair_cancel (p q rest : Bool) (h : p = q) :
    Bool.xor (Bool.xor rest p) q = rest := by
  subst q
  cases p <;> cases rest <;> decide

theorem phase_zero_cancel (rest contribution : Bool) (h : contribution = false) :
    Bool.xor rest contribution = rest := by
  subst contribution
  cases rest <;> decide

theorem coefficient_distributes (a b monomial : Bool) :
    Bool.xor (a && monomial) (b && monomial) = ((Bool.xor a b) && monomial) := by
  cases a <;> cases b <;> cases monomial <;> decide

theorem phase_move (a b c : Bool) :
    Bool.xor (Bool.xor a b) c = Bool.xor (Bool.xor a c) b := by
  cases a <;> cases b <;> cases c <;> decide

theorem guard_refinement (active narrower action : Bool)
    (h : (active && action && !narrower) = false) :
    (active && action) = (active && narrower && action) := by
  cases active <;> cases narrower <;> cases action <;> simp_all

-- PR45 actual phase gates 20702 and 20722: the effective phase predicates
-- agree on every legal x and potential HMR history according to the BDD.
-- We do not assert the guard equality for arbitrary independent q/m values.
theorem actual_pair_20702_20722
    (g1 g2 a1 b1 c1 a2 b2 c2 p : Bool)
    (h : (g1 && a1 && b1 && c1) = (g2 && a2 && b2 && c2)) :
    Bool.xor (Bool.xor p (g1 && a1 && b1 && c1)) (g2 && a2 && b2 && c2) = p :=
  phase_pair_cancel _ _ _ h

-- Actual phase-parent CCX at native index 5843; 4 free X/CX updates.
theorem actual_cofactor_5843 (q3 q11 q12 q16 q24 q33 : Bool)
    (h : (q16 && q33) = (Bool.xor (Bool.xor (Bool.xor q11 q12) q24) q33)) :
    Bool.xor q3 (q16 && q33) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor q3 q11) q12) q24) q33) := by
  bv_decide

-- Actual phase-parent CCX at native index 6002; 4 free X/CX updates.
theorem actual_cofactor_6002 (q3 q10 q12 q16 q24 q33 : Bool)
    (h : (q24 && q16) = (Bool.xor (Bool.xor (Bool.xor q10 q12) q16) q33)) :
    Bool.xor q3 (q24 && q16) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor q3 q10) q12) q16) q33) := by
  bv_decide

-- Actual phase-parent CCX at native index 7827; 6 free X/CX updates.
theorem actual_cofactor_7827 (q3 q7 q10 q13 q19 q33 : Bool)
    (h : (q19 && q7) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor true q7) q10) q13) q19) q33)) :
    Bool.xor q3 (q19 && q7) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor q3 true) q7) q10) q13) q19) q33) := by
  bv_decide

-- Actual phase-parent CCX at native index 8081; 4 free X/CX updates.
theorem actual_cofactor_8081 (q3 q6 q20 q25 q33 q34 : Bool)
    (h : (q25 && q6) = (Bool.xor (Bool.xor (Bool.xor q3 q6) q20) q33)) :
    Bool.xor q34 (q25 && q6) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor q34 q3) q6) q20) q33) := by
  bv_decide

-- Actual phase-parent CCX at native index 8150; 4 free X/CX updates.
theorem actual_cofactor_8150 (q3 q8 q20 q31 q33 q34 : Bool)
    (h : (q31 && q20) = (Bool.xor (Bool.xor (Bool.xor q3 q20) q33) q34)) :
    Bool.xor q8 (q31 && q20) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor q8 q3) q20) q33) q34) := by
  bv_decide

-- Actual phase-parent CCX at native index 8209; 4 free X/CX updates.
theorem actual_cofactor_8209 (q3 q8 q9 q15 q33 q34 : Bool)
    (h : (q9 && q34) = (Bool.xor (Bool.xor (Bool.xor q3 q8) q33) q34)) :
    Bool.xor q15 (q9 && q34) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor q15 q3) q8) q33) q34) := by
  bv_decide

-- Actual phase-parent CCX at native index 9639; 1 free X/CX updates.
theorem actual_cofactor_9639 (q26 q27 q30 q33 : Bool)
    (h : (q26 && q27) = q33) :
    Bool.xor q30 (q26 && q27) = (Bool.xor q30 q33) := by
  bv_decide

-- Actual phase-parent CCX at native index 13305; 4 free X/CX updates.
theorem actual_cofactor_13305 (q0 q3 q4 q19 q27 q29 : Bool)
    (h : (q4 && q0) = (Bool.xor (Bool.xor (Bool.xor q3 q4) q19) q27)) :
    Bool.xor q29 (q4 && q0) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor q29 q3) q4) q19) q27) := by
  bv_decide

end GVQCCV9
