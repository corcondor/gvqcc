import Init

/-! Family-C m=6, MAIN: row 25 retirement certificate.
Only the arithmetic chart and local Boolean gate semantics are certified.
No theorem here proves the physical MAIN schedule or its width. -/
namespace GVQCC.FamilyCRow25

def bx (a b : Bool) : Bool := Bool.xor a b
def maj (a b c : Bool) : Bool := bx c (bx a c && bx b c)
def borrow (a d b : Bool) : Bool := maj (!a) d b

-- A sign copy may acquire independent information during an update.
theorem copy_after_update (s x : Bool) : bx s (bx s x) = x := by
  cases s <;> cases x <;> decide

theorem stale_copy_counterexample : bx false (bx false true) = true := by decide

-- Exact initial-window algebra; a and s are the two high input bits.
theorem first_window_identity (a s v : Int) :
    a + 254*s - (129 + 2*v) =
      (1-a) + 2*(a-s-65-v) + 256*s := by omega

-- The fixed first two NR subtractions (b=26,25).
-- U is the signed 21-bit HO word, h is floor(U/2^18).
theorem row25_word_formula (u v : Int) :
    (17179869184 + 128*u - 3*(129+2*v)*33554432) / 33554432 =
      125 + u / 262144 - 6*v := by omega

-- Normalize the bounded remainders explicitly; omega's linear relaxation
-- alone does not enforce the required integral quotient cases.
private theorem add_self_mod (x n : Int) : (x+n) % n = x % n := by
  rw [Int.add_emod]
  simp

private theorem mod_signed (x n : Int) (hl : -n <= x) (hu : x < n) :
    x % n = if 0 <= x then x else x+n := by
  by_cases h : 0 <= x
  · simpa only [if_pos h] using (Int.emod_eq_of_lt h hu)
  · rw [if_neg h]
    calc
      x % n = (x+n) % n := (add_self_mod x n).symm
      _ = x+n := Int.emod_eq_of_lt (by omega) (by omega)

private theorem mod_unsigned (x n : Int) (hl : 0 <= x) (hu : x < 2*n) :
    x % n = if x < n then x else x-n := by
  by_cases h : x < n
  · simpa only [if_pos h] using (Int.emod_eq_of_lt hl h)
  · rw [if_neg h]
    have he := add_self_mod (x-n) n
    have hh : x-n+n = x := by omega
    rw [hh] at he
    exact he.trans (Int.emod_eq_of_lt (by omega) (by omega))

-- An independently useful, exact bounded arithmetic theorem.
-- r is the residue modulo 512; bit8 is r >= 256,
-- bit7 is r % 256 >= 128, v5 is v >= 32, v4 is v % 32 >= 16.
theorem row25_sign_relation (v h r : Int)
    (hv0 : 0 <= v) (hv1 : v < 64)
    (hh0 : -4 <= h) (hh1 : h <= 3)
    (hr : r = (125+h-6*v) % 512) :
    (256 <= r) <->
      ((32 <= v /\ Not (128 <= r % 256 /\ 16 <= v % 32)) \/
       (Not (32 <= v) /\ (128 <= r % 256 /\ 16 <= v % 32))) := by
  have hr0 : 0 <= r := by
    rw [hr]
    exact Int.emod_nonneg _ (by decide)
  have hr1 : r < 512 := by
    rw [hr]
    exact Int.emod_lt_of_pos _ (by decide)
  have hr' := hr.trans (mod_signed (125+h-6*v) 512 (by omega) (by omega))
  have hrmod := mod_unsigned r 256 hr0 (by omega)
  have hvmod := mod_unsigned v 32 hv0 (by omega)
  rw [hrmod, hvmod]
  by_cases hq : 0 <= 125+h-6*v <;>
    by_cases hv32 : v < 32 <;>
    by_cases hr256 : r < 256 <;>
    simp [hq, hv32, hr256] at hr' ⊢ <;> omega

private theorem xor_bridge (P Q A B : Prop)
    [Decidable P] [Decidable Q] [Decidable A] [Decidable B]
    (H : P <-> ((Q /\ Not (A /\ B)) \/ (Not Q /\ (A /\ B)))) :
    decide P = bx (decide Q) (decide A && decide B) := by
  by_cases p : P <;> by_cases q : Q <;> by_cases a : A <;> by_cases b : B <;>
    simp_all [bx, Bool.xor]

-- Boolean bridge between the integer certificate and the gate predicate.
theorem row25_bool_relation (v h r : Int)
    (hv0 : 0 <= v) (hv1 : v < 64)
    (hh0 : -4 <= h) (hh1 : h <= 3)
    (hr : r = (125+h-6*v) % 512) :
    decide (256 <= r) =
      bx (decide (32 <= v))
        (decide (128 <= r % 256) && decide (16 <= v % 32)) := by
  exact xor_bridge _ _ _ _ (row25_sign_relation v h r hv0 hv1 hh0 hh1 hr)

-- Reversible clearing and reconstruction, when the relation is true at this cut.
theorem clear_top (r8 r7 v5 v4 : Bool)
    (hr : r8 = bx v5 (r7 && v4)) :
    bx (bx r8 v5) (r7 && v4) = false := by
  subst r8
  cases r7 <;> cases v5 <;> cases v4 <;> decide

theorem rebuild_top (r7 v5 v4 : Bool) :
    bx (bx false v5) (r7 && v4) = bx v5 (r7 && v4) := by
  cases r7 <;> cases v5 <;> cases v4 <;> decide

-- X-measurement yields a phase m*r8. Conditional Z(v5) and CZ(r7,v4)
-- cancel it for both outcomes; r7/v4/v5 must still mean the same values.
theorem hmr_top_phase (r8 r7 v5 v4 m : Bool)
    (hr : r8 = bx v5 (r7 && v4)) :
    bx (m && r8) (bx (m && v5) (m && (r7 && v4))) = false := by
  subst r8
  cases r7 <;> cases v5 <;> cases v4 <;> cases m <;> decide

-- The untransported relation can fail once r7 changes.
theorem stale_phase_counterexample :
    bx (true && true)
      (bx (true && false) (true && (false && true))) = true := by decide

-- Upstream s-free borrow ladder for repeated sign bits.
theorem ladder_first (a s v0 : Bool) :
    !(bx s (borrow s v0 (!a))) = (bx a s && !(bx v0 s)) := by
  cases a <;> cases s <;> cases v0 <;> decide

theorem ladder_step (s vi b : Bool) :
    !(bx s (borrow s vi b)) = (!(bx s b) && !(bx s vi)) := by
  cases s <;> cases vi <;> cases b <;> decide

theorem ladder_anchor (s v0 vi t : Bool) (ha : t = true -> s = v0) :
    (t && !(bx s vi)) = (t && !(bx v0 vi)) := by
  cases t with
  | false => rfl
  | true =>
    have H := ha rfl
    rw [H]

end GVQCC.FamilyCRow25

#print axioms GVQCC.FamilyCRow25.copy_after_update
#print axioms GVQCC.FamilyCRow25.stale_copy_counterexample
#print axioms GVQCC.FamilyCRow25.first_window_identity
#print axioms GVQCC.FamilyCRow25.row25_word_formula
#print axioms GVQCC.FamilyCRow25.row25_sign_relation
#print axioms GVQCC.FamilyCRow25.row25_bool_relation
#print axioms GVQCC.FamilyCRow25.clear_top
#print axioms GVQCC.FamilyCRow25.rebuild_top
#print axioms GVQCC.FamilyCRow25.hmr_top_phase
#print axioms GVQCC.FamilyCRow25.stale_phase_counterexample
#print axioms GVQCC.FamilyCRow25.ladder_first
#print axioms GVQCC.FamilyCRow25.ladder_step
#print axioms GVQCC.FamilyCRow25.ladder_anchor
