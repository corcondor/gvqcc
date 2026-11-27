import Mathlib

namespace GVQCC.HermiteProjection

variable {F : Type*} [Field F]

/-- A conjugate-root component obeys the quadratic shift recurrence. -/
theorem quadratic_component (a z k : F) (j : ℕ)
    (hz : z^2 = z+k) :
    a*z^(j+2) = a*z^(j+1)+k*(a*z^j) := by
  rw [pow_add z j 2, pow_add z j 1, pow_one, hz]
  ring

/-- On the first-pole family N=a*g*X^n, the quotient T has degree 35
    and v*T(z)=z^32 at a simple root z of g. This lemma proves the
    scalar identity; it does not claim that the donor always projects v. -/
theorem single_jet_product (a z d : F) (n : ℕ)
    (ha : a ≠ 0) (hd : d ≠ 0) (hn : n ≤ 32) :
    (a*z^n/d)*(z^(32-n)*d/a) = z^32 := by
  calc
    _ = z^n*z^(32-n) := by field_simp [ha, hd]
    _ = z^(n+(32-n)) := by rw [pow_add]
    _ = z^32 := by rw [Nat.add_sub_of_le hn]

theorem restore_derivative (v t z : F) (ht : t ≠ 0)
    (hv : v*t = z^32) :
    z^32/t = v := by
  apply (div_eq_iff ht).mpr
  exact hv.symm

/-- Recover the scaled locator from a first derivative at a zero numerator. -/
theorem allpole_locator (c gp d : F)
    (hc : c ≠ 0) (hg : gp ≠ 0) (hd : d ≠ 0) :
    gp/(c*gp/d) = d/c := by
  field_simp [hc, hg, hd]

/-- Leading two coefficients of D/c from c and c*d_34. -/
theorem leading_coefficient (c d : F) (hc : c ≠ 0) :
    (c*d)/c^2 = d/c := by
  field_simp [hc]

/-- Forney magnitude for N=cG and T=D/c. -/
theorem allpole_magnitude (c x g d : F)
    (hc : c ≠ 0) (hx : x ≠ 0) (hg : g ≠ 0) (hd : d ≠ 0) :
    (x*g*(d/c))⁻¹ = c/(x*g*d) := by
  field_simp [hc, hx, hg, hd]

/-- The repair's selection is invariant under translation in the kernel
    of the observed coordinates. -/
theorem observed_unchanged {A B : Type*} [AddCommGroup A] [AddCommGroup B]
    (L : A →+ B) (s p : A) (hp : L p = 0) :
    L (s+p) = L s := by rw [map_add, hp, add_zero]

theorem xor_repair_involution {A B : Type*} [AddCommGroup A] [AddCommGroup B]
    (L : A →+ B) (r : B → A) (s : A)
    (hk : ∀ x, L (r x) = 0) (h2 : ∀ x, r x+r x = 0) :
    (s+r (L s))+r (L (s+r (L s))) = s := by
  rw [observed_unchanged L s (r (L s)) (hk (L s)), add_assoc, h2, add_zero]

theorem hmr_repay (p m x : Bool) :
    (p ^^ (m && x)) ^^ (m && x) = p := by
  cases p <;> cases m <;> cases x <;> decide

/-- The nonzero reciprocal jet comparison can use one bilinear
    residual instead of another field division. -/
theorem cross_jet (v t a ap tp : F) (ht : t ≠ 0) :
    v = (a*tp+ap*t)/t^2 ↔ v*t^2 = a*tp+ap*t := by
  constructor
  · intro h
    exact (div_eq_iff (pow_ne_zero 2 ht)).mp h.symm |>.symm
  · intro h
    exact ((div_eq_iff (pow_ne_zero 2 ht)).mpr h.symm).symm

end GVQCC.HermiteProjection
#print axioms GVQCC.HermiteProjection.quadratic_component
#print axioms GVQCC.HermiteProjection.single_jet_product
#print axioms GVQCC.HermiteProjection.restore_derivative
#print axioms GVQCC.HermiteProjection.allpole_locator
#print axioms GVQCC.HermiteProjection.leading_coefficient
#print axioms GVQCC.HermiteProjection.allpole_magnitude
#print axioms GVQCC.HermiteProjection.observed_unchanged
#print axioms GVQCC.HermiteProjection.xor_repair_involution
#print axioms GVQCC.HermiteProjection.hmr_repay

#print axioms GVQCC.HermiteProjection.cross_jet
