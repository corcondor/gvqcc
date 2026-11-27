import Mathlib
namespace GVQCC.Rewrite
set_option autoImplicit false

theorem xor_cancel (t u : Bool) : (t ^^ u) ^^ u = t := by
  cases t <;> cases u <;> decide

theorem xor_transport (t u v : Bool) : (t ^^ u) ^^ v = (t ^^ v) ^^ u := by
  cases t <;> cases u <;> cases v <;> decide

theorem guarded_xor_cancel (t a b guard : Bool) :
    (t ^^ (guard && a && b)) ^^ (guard && a && b) = t := by
  cases t <;> cases a <;> cases b <;> cases guard <;> decide

theorem hmr_dead_write (t a b m : Bool) :
    m && (t ^^ (a && b)) = ((m && t) ^^ (m && a && b)) := by
  cases t <;> cases a <;> cases b <;> cases m <;> decide

theorem hmr_guarded_dead_write (t a b m guard : Bool) :
    m && (t ^^ (guard && a && b)) =
      ((m && t) ^^ (m && guard && a && b)) := by
  cases t <;> cases a <;> cases b <;> cases m <;> cases guard <;> decide

/-- A stable, commuting involution surrounding an intervening segment cancels. -/
theorem involution_transport {S : Type*} (g f : S → S)
    (hg : ∀ s, g (g s) = s)
    (hcomm : ∀ s, g (f s) = f (g s)) (s : S) :
    g (f (g s)) = f s := by
  rw [hcomm, hg]

/-- Under the HMR model the reset target is identical and phase debt is repaid. -/
theorem hmr_step (t a b m p : Bool) :
    (false, p ^^ (m && (t ^^ (a && b)))) =
      (false, (p ^^ (m && t)) ^^ (m && a && b)) := by
  cases t <;> cases a <;> cases b <;> cases m <;> cases p <;> decide

end GVQCC.Rewrite
#print axioms GVQCC.Rewrite.xor_cancel
#print axioms GVQCC.Rewrite.xor_transport
#print axioms GVQCC.Rewrite.guarded_xor_cancel
#print axioms GVQCC.Rewrite.hmr_dead_write
#print axioms GVQCC.Rewrite.hmr_guarded_dead_write
#print axioms GVQCC.Rewrite.involution_transport
#print axioms GVQCC.Rewrite.hmr_step
