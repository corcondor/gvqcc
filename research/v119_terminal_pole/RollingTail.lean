import Mathlib

namespace GVQCC.RollingTail
variable {F : Type*} [Field F]

/-- Fraction-free continuants: update the determinant of the leading two
coefficient rows, without an inverse at each step. -/
theorem determinant_update (n d ns ds h0 h1 : F)
    (hc : (2 : F) = 0) :
    let dp := n+h1*d
    let dsp := ns+h1*ds+h0*d+dp
    ds*dp+d*dsp = (ns*d+n*ds)+h0*d^2+d*dp := by
  dsimp
  linear_combination (h1*d*ds)*hc

/-- Two consecutive cross terms collapse to a single square term. -/
theorem pair_telescope (r q h : F) (hc : (2 : F) = 0) :
    r*q+q*(r+h*q) = h*q^2 := by
  linear_combination (r*q)*hc

/-- In the last repeated-node pole, D33=p*g and its subleading coefficient
is p. The final cross term removes the n3*p contribution. -/
theorem recover_subleading (p q n2 L : F) (hc : (2 : F) = 0)
    (hp : p ≠ 0) (hL : L = n2*p+q*p) :
    (L+p*q)/p = n2 := by
  apply (div_eq_iff hp).2
  linear_combination hL+(p*q)*hc

/-- Finite terminal chart, including the unnormalized factor p. -/
theorem recover_finite_value (z n0 u : F) (hz : z ≠ 0)
    (hu : u*n0 = z) : z/u = n0 := by
  have hnu : u ≠ 0 := by
    intro h
    apply hz
    simpa [h] using hu.symm
  exact (div_eq_iff hnu).2 (by simpa [mul_comm] using hu.symm)

/-- Zero-value reciprocal chart. The field's totalized division also recovers
the double-zero case; no division-by-zero exception is needed here. -/
theorem recover_zero_tail (z n1 v : F) (hz : z ≠ 0)
    (hv : v = z/n1) : z/v = n1 := by
  rw [hv]
  by_cases hn : n1 = 0
  · simp [hn]
  · apply (div_eq_iff (div_ne_zero hz hn)).2
    calc
      z = (z/n1)*n1 := (div_mul_cancel₀ z hn).symm
      _ = n1*(z/n1) := mul_comm _ _

/-- A confluent pair is reconstructed without dividing at the second visit. -/
theorem repeated_pair_reconstruct (g h p n d : F) (hd : d = p*g) :
    h*n+g*d = h*n+p*g^2 := by
  rw [hd]
  ring

/-- Store one product in a clean idle wire and reuse it at two paid sites.
For every outcome m, HMR and the correcting controlled phase cancel. -/
theorem product_retention (a b x y m : Bool) :
    let z := a && b
    (Bool.xor x z, Bool.xor y z, Bool.xor (m && z) (m && a && b)) =
    (Bool.xor x (a && b), Bool.xor y (a && b), false) := by
  cases a <;> cases b <;> cases x <;> cases y <;> cases m <;> decide

end GVQCC.RollingTail

#print axioms GVQCC.RollingTail.determinant_update
#print axioms GVQCC.RollingTail.pair_telescope
#print axioms GVQCC.RollingTail.recover_subleading
#print axioms GVQCC.RollingTail.recover_finite_value
#print axioms GVQCC.RollingTail.recover_zero_tail
#print axioms GVQCC.RollingTail.repeated_pair_reconstruct
#print axioms GVQCC.RollingTail.product_retention
