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
  by_cases hv16 : v < 16
  · omega
  · by_cases hv32 : v < 32
    · omega
    · by_cases hv48 : v < 48
      · omega
      · omega

-- Boolean bridge between the integer certificate and the gate predicate.
theorem row25_bool_relation (v h r : Int)
    (hv0 : 0 <= v) (hv1 : v < 64)
    (hh0 : -4 <= h) (hh1 : h <= 3)
    (hr : r = (125+h-6*v) % 512) :
    decide (256 <= r) =
      bx (decide (32 <= v))
        (decide (128 <= r % 256) && decide (16 <= v % 32)) := by
  have H := row25_sign_relation v h r hv0 hv1 hh0 hh1 hr
  by_cases p : 256 <= r <;> by_cases q : 32 <= v <;>
    by_cases a : 128 <= r % 256 <;> by_cases b : 16 <= v % 32 <;>
    simp_all [bx, Bool.xor]

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
