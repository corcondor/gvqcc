import Mathlib

namespace GVQCC.AdaptiveHalfGCD

section Algebra
variable {R : Type*} [CommRing R]

/-- A single normalized divisor handles the high quotient and the
    remaining degree-dependent low quotient without shifting the dividend. -/
theorem normalized_split (A B Qh Ql Rmid Rem x : R) (d : Nat)
    (hh : A = (x^d*B)*Qh + Rmid)
    (hl : Rmid = B*Ql + Rem) :
    A = B*(x^d*Qh+Ql)+Rem := by
  rw [hh, hl]
  ring

theorem quotient_recover (B Qh Ql Rem x : R) (d : Nat) :
    (x^d*B)*Qh+(B*Ql+Rem) = B*(x^d*Qh+Ql)+Rem := by ring

theorem high_low_fusion (a b c d x y : R) :
    (a+x*c)*(b+x*d) + y =
      a*b+y+x*(a*d+c*b+x*c*d) := by ring

theorem shift_divisor (B q r x : R) (d j : Nat) :
    (x^d*B)*q*x^j+r = B*(x^(d+j)*q)+r := by
  rw [pow_add]
  ring

theorem zero_mask_product (a b : R) : (0*a)*b = 0 := by simp

theorem masked_product (g : Bool) (a b : R) :
    (if g then a else 0)*b = if g then a*b else 0 := by
  cases g <;> simp

theorem masked_dirty_target (g : Bool) (a b y : R) :
    y + (if g then a else 0)*b = if g then y+a*b else y := by
  cases g <;> simp

theorem masked_quotient_restore (g : Bool) (a q : R) :
    (if g then q else a) = a + (if g then q-a else 0) := by
  cases g <;> simp

theorem two_rhs_accumulate (a b c d y : R) :
    (y+a*b)+c*d = y+(a*b+c*d) := by ring

theorem shear_output_restore (x y w p : R) :
    (y-w*x)+w*(x+p) = y+w*p := by ring

theorem shear_output_transport (x y w v : R) :
    (y-w*x)+(w-v)*x = y-v*x := by ring

theorem fractional_step (a x v : R) :
    a*(1+x*v) = a+x*(a*v) := by ring

theorem cf_cross (a x u v : R) :
    a*(1+x*u)*(1+x*v) =
      a+a*x*(u+v)+a*x^2*u*v := by ring

/-- Greedy binary degree normalization maintains the next bound. -/
theorem binary_degree_step (d p : Nat) (h : d < 2*p) (hp : 0 < p) :
    (if p ≤ d then d-p else d) < p := by
  split <;> omega

theorem binary_degree_reconstruct (d p : Nat) :
    (if p ≤ d then p else 0)+(if p ≤ d then d-p else d)=d := by
  split <;> omega

theorem zero_test_permutation {I V : Type*} [Zero V]
    (P : I → I) (w : I → V) (i : I) :
    ((w ∘ P) i = 0) ↔ w (P i) = 0 := Iff.rfl

theorem square_add_char2 (a b : R) (h2 : (2:R)=0) :
    (a+b)^2 = a^2+b^2 := by
  calc
    (a+b)^2 = a^2+b^2+2*a*b := by ring
    _ = a^2+b^2 := by rw [h2]; simp

theorem frobenius_add (a b : R) (h2 : (2:R)=0) (n : Nat) :
    (a+b)^(2^n) = a^(2^n)+b^(2^n) := by
  induction n with
  | zero => simp
  | succ n ih =>
    calc
      (a+b)^(2^(n+1)) = ((a+b)^(2^n))^2 := by rw [pow_succ, pow_mul]
      _ = (a^(2^n)+b^(2^n))^2 := by rw [ih]
      _ = (a^(2^n))^2+(b^(2^n))^2 := square_add_char2 _ _ h2
      _ = a^(2^(n+1))+b^(2^(n+1)) := by simp only [pow_succ, pow_mul]

theorem fermat_chain (u : R) :
    ((u^3)^5)^17 = u^255 := by
  rw [← pow_mul, ← pow_mul]

/-- In a truncated characteristic-two series ring, x^256=0.
    Normalized unit inversion is three in-place Frobenius-power maps. -/
theorem unit_inverse_chain (x v : R) (h2 : (2:R)=0) (hx : x^256=0) :
    (1+x*v)*((((1+x*v)^3)^5)^17)=1 := by
  rw [fermat_chain, ← pow_succ']
  have h := frobenius_add (1:R) (x*v) h2 8
  change (1+x*v)^256 = 1^256+(x*v)^256 at h
  change (1+x*v)^256=1
  rw [h, mul_pow, hx]
  simp

theorem unit_inverse_involution (a b c : R) (hab : a*b=1) (hbc : b*c=1) :
    c=a := by
  calc
    c = (a*b)*c := by rw [hab, one_mul]
    _ = a*(b*c) := by ring
    _ = a := by rw [hbc, mul_one]

end Algebra

section Field
variable {F : Type*} [Field F]

/-- Keep pivot scale outside the recursively inverted tail. -/
theorem projective_reciprocal (a u v : F) (ha : a≠0) (h : u*v=1) :
    (a*u)*(a⁻¹*v)=1 := by
  calc
    (a*u)*(a⁻¹*v) = (a*a⁻¹)*(u*v) := by ring
    _ = 1 := by rw [mul_inv_cancel₀ ha, h, one_mul]

theorem cf_recover (a x v : F) (h : 1+x*v≠0) :
    (a/(1+x*v))*(1+x*v)=a := div_mul_cancel₀ _ h

end Field
end GVQCC.AdaptiveHalfGCD

#print axioms GVQCC.AdaptiveHalfGCD.normalized_split
#print axioms GVQCC.AdaptiveHalfGCD.quotient_recover
#print axioms GVQCC.AdaptiveHalfGCD.high_low_fusion
#print axioms GVQCC.AdaptiveHalfGCD.shift_divisor
#print axioms GVQCC.AdaptiveHalfGCD.zero_mask_product
#print axioms GVQCC.AdaptiveHalfGCD.masked_product
#print axioms GVQCC.AdaptiveHalfGCD.masked_dirty_target
#print axioms GVQCC.AdaptiveHalfGCD.masked_quotient_restore
#print axioms GVQCC.AdaptiveHalfGCD.two_rhs_accumulate
#print axioms GVQCC.AdaptiveHalfGCD.shear_output_restore
#print axioms GVQCC.AdaptiveHalfGCD.shear_output_transport
#print axioms GVQCC.AdaptiveHalfGCD.fractional_step
#print axioms GVQCC.AdaptiveHalfGCD.cf_cross
#print axioms GVQCC.AdaptiveHalfGCD.binary_degree_step
#print axioms GVQCC.AdaptiveHalfGCD.binary_degree_reconstruct
#print axioms GVQCC.AdaptiveHalfGCD.zero_test_permutation
#print axioms GVQCC.AdaptiveHalfGCD.square_add_char2
#print axioms GVQCC.AdaptiveHalfGCD.frobenius_add
#print axioms GVQCC.AdaptiveHalfGCD.fermat_chain
#print axioms GVQCC.AdaptiveHalfGCD.unit_inverse_chain
#print axioms GVQCC.AdaptiveHalfGCD.unit_inverse_involution
#print axioms GVQCC.AdaptiveHalfGCD.projective_reciprocal
#print axioms GVQCC.AdaptiveHalfGCD.cf_recover
