import Mathlib
namespace GVQCC.ZeroSafeJet
variable {F : Type*} [Field F]

/-- Safe scale uses the existing zero fiber, not the zero multiplier. -/
noncomputable def safeInv (u : F) : F := by
  classical
  exact if u = 0 then 1 else u⁻¹

theorem safeInv_cancel (u : F) :
    safeInv u * safeInv (u⁻¹) = 1 := by
  classical
  by_cases hu : u = 0
  · simp [safeInv, hu]
  · have hi : u⁻¹ ≠ 0 := inv_ne_zero hu
    simp [safeInv, hu, hi]

noncomputable def jet (p : F × F) : F × F :=
  (p.1⁻¹, p.2 * safeInv p.1 ^ 2)

theorem jet_involutive (u v : F) :
    jet (jet (u, v)) = (u, v) := by
  change ((u⁻¹)⁻¹, (v * safeInv u ^ 2) * safeInv (u⁻¹) ^ 2) = (u, v)
  rw [inv_inv, mul_assoc, ← mul_pow, safeInv_cancel, one_pow, mul_one]

theorem jet_zero_fiber (v : F) : jet (0, v) = (0, v) := by
  simp [jet, safeInv]

/-- Termination is a fixed point, but a general zero fiber must not be cleared. -/
theorem jet_terminal : jet (0, 0) = ((0 : F), (0 : F)) :=
  jet_zero_fiber 0

theorem zero_collapse_not_injective :
    ¬ Function.Injective (fun p : F × F => (p.1⁻¹, p.2 * (p.1⁻¹)^2)) := by
  intro h
  have he : ((0 : F), (0 : F)) = (0, 1) := h (by simp)
  exact zero_ne_one (congrArg Prod.snd he)

/-- The orientation matches the native inverse head: D = g Q + h N. -/
theorem reverse_inverse_head {R : Type*} [CommRing R]
    (N D h g Q : R) (h2 : (2 : R) = 0) (step : g*Q = D+h*N) :
    g*Q+h*N = D := by
  rw [step]
  calc
    D + h*N + h*N = D + 2*(h*N) := by ring
    _ = D := by rw [h2, zero_mul, add_zero]

/-- A single reciprocal of q serves both coordinates of the post-transport. -/
theorem shared_post_inverse (q a b : F) (hq : q ≠ 0) :
    ((q*a)/q, (a+q*b-(q*a)/q)/q) = (a,b) := by
  have ha : q*a/q = a := by field_simp
  rw [ha]
  have hb : (a+q*b-a)/q = b := by
    field_simp
    ring
  rw [hb]

end GVQCC.ZeroSafeJet

#print axioms GVQCC.ZeroSafeJet.safeInv_cancel
#print axioms GVQCC.ZeroSafeJet.jet_involutive
#print axioms GVQCC.ZeroSafeJet.jet_zero_fiber
#print axioms GVQCC.ZeroSafeJet.jet_terminal
#print axioms GVQCC.ZeroSafeJet.zero_collapse_not_injective
#print axioms GVQCC.ZeroSafeJet.reverse_inverse_head
#print axioms GVQCC.ZeroSafeJet.shared_post_inverse
