import Mathlib

namespace GVQCC.MultiAnchor279

section Field
variable {F : Type*} [Field F]

theorem anchor_value (r c u : F) (h2 : (2 : F) = 0) :
    r + (r+c*u) + c*u = 0 := by
  calc
    _ = 2*(r+c*u) := by ring
    _ = _ := by rw [h2, zero_mul]

theorem slope_residual (r t c d u : F) (h2 : (2 : F) = 0)
    (hd : c+d ≠ 0) :
    r+(t+d*u)+c*u = 0 ↔ (r+t)/(c+d) = u := by
  rw [div_eq_iff hd]
  have he : r+(t+d*u)+c*u = (r+t)+u*(c+d) := by ring
  rw [he]
  constructor
  · intro h
    calc
      r+t = r+t + 2*(u*(c+d)) := by rw [h2,zero_mul,add_zero]
      _ = ((r+t)+u*(c+d))+u*(c+d) := by ring
      _ = u*(c+d) := by rw [h,zero_add]
  · intro h
    rw [h]
    calc
      _ = 2*(u*(c+d)) := by ring
      _ = 0 := by rw [h2,zero_mul]

theorem origin_slope (t d u : F) (h2 : (2 : F) = 0)
    (hd : d ≠ 0) : t+d*u=0 ↔ t/d=u := by
  simpa only [zero_add,add_zero,zero_mul] using
    (slope_residual (F:=F) 0 t 0 d u h2 (by simpa only [zero_add] using hd))

end Field

/-- The anchor gives one extra zero, while the revived mu leaf costs one.
The extra virtual origin in the histogram counts the lambda-zero bonus. -/
theorem score_identity (N n b : Nat) (hn : n+1 ≤ N) (hb : b ≤ 1) :
    11*(N-(n+1)) + 11*(1-b) + 11 = 11*(N+1-(n+b)) := by omega

theorem baseline_identity (N n b : Nat) (hn : n ≤ N) (hb : b ≤ 1) :
    11*(N-n)+11*(1-b)=11*(N+1-(n+b)) := by omega

theorem strict_score_saves (N old new : Nat) (h : old < new)
    (hn : new ≤ N+1) :
    11*(N+1-new) < 11*(N+1-old) := by omega

def bestScore (old : Nat) (cs : List Nat) : Nat := cs.foldl max old

theorem fold_max_monotone (old : Nat) (cs : List Nat) :
    old ≤ bestScore old cs := by
  induction cs generalizing old with
  | nil => exact Nat.le_refl _
  | cons c cs ih =>
    exact le_trans (le_max_left old c) (ih (max old c))

theorem padded_count (n : Nat) (h : n ≤ 4024) :
    n+72 ≤ 4096 := by omega

section Boolean
def cx (a b : Bool) : Bool := Bool.xor a b

theorem swap_three (a b : Bool) :
    let d := cx a b
    let e := cx d a
    (e,cx e d)=(b,a) := by
  cases a <;> cases b <;> decide

theorem fredkin_three (c a b : Bool) :
    let d := cx a b
    let e := cx (c && d) a
    (e,cx e d) = if c then (b,a) else (a,b) := by
  cases c <;> cases a <;> cases b <;> decide

theorem product_conjugation (a b t u : Bool) :
    let p := a && b
    let t' := cx p t
    (cx p t',cx t' u) = (t,cx p (cx t u)) := by
  cases a <;> cases b <;> cases t <;> cases u <;> decide

theorem fanout_two (a b t u : Bool) :
    let p := a && b
    (cx p t,cx p u) = (cx p t,cx (cx p t) (cx t u)) := by
  cases a <;> cases b <;> cases t <;> cases u <;> decide

theorem linear_product (a b c t : Bool) :
    cx (a && b) (cx (a && c) t) = cx (a && cx b c) t := by
  cases a <;> cases b <;> cases c <;> cases t <;> decide

theorem linear_phase (a b c d : Bool) :
    cx (a && b && c) (a && b && d) = (a && b && cx c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide
end Boolean

theorem compact_ops : 67549292-67262375=286917 := by decide
theorem frame_ops : 2*(133084+108)+2*43=266470 := by decide
theorem paid_samples : 647479289-647461832=17457 := by decide

#print axioms anchor_value
#print axioms slope_residual
#print axioms origin_slope
#print axioms score_identity
#print axioms baseline_identity
#print axioms strict_score_saves
#print axioms fold_max_monotone
#print axioms padded_count
#print axioms swap_three
#print axioms fredkin_three
#print axioms product_conjugation
#print axioms fanout_two
#print axioms linear_product
#print axioms linear_phase
#print axioms compact_ops
#print axioms frame_ops
#print axioms paid_samples

end GVQCC.MultiAnchor279
