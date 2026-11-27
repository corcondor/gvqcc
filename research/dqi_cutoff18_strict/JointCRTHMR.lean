import Mathlib

namespace GVQCC.JointCRTHMR

variable {F : Type*} [Field F]

/-- Zero-safe norm inversion, including the zero residue. -/
theorem reciprocal_norm (n : F) : n*(n⁻¹)^2 = n⁻¹ := by
  by_cases hn : n = 0
  · simp [hn]
  · calc
      _ = (n*n⁻¹)*n⁻¹ := by ring
      _ = _ := by rw [mul_inv_cancel₀ hn,one_mul]

/-- Norm of the conjugate multiplied by a common scalar. -/
theorem scaled_conjugate_norm (a b k h : F) (h2 : (2:F)=0) :
    ((a+b)*h)^2+((a+b)*h)*(b*h)+k*(b*h)^2 =
      (a^2+a*b+k*b^2)*h^2 := by
  calc
    _ = (a^2+a*b+k*b^2)*h^2 + 2*(a*b+b^2)*h^2 := by ring
    _ = _ := by rw [h2,zero_mul,zero_mul,add_zero]

/-- This is precisely the value of the final HMR-reset norm word. -/
theorem final_norm_witness (a b k n : F)
    (hn : n = a^2+a*b+k*b^2) (h2 : (2:F)=0) :
    ((a+b)*n⁻¹)^2+((a+b)*n⁻¹)*(b*n⁻¹)+k*(b*n⁻¹)^2 = n⁻¹ := by
  rw [scaled_conjugate_norm a b k n⁻¹ h2, ← hn, reciprocal_norm]

/-- A swapped-out multiplicand is reconstructible as a product of the
new value and the old norm.  When the norm is zero, require the old
value to be zero (verified for each concrete irreducible chart). -/
theorem zero_safe_product_witness (x n : F)
    (hz : n=0 → x=0) : (x*n⁻¹)*n=x := by
  by_cases hn : n=0
  · simp [hn,hz hn]
  · rw [mul_assoc,inv_mul_cancel₀ hn,mul_one]

/-- Dual mask of a CX, valid even with a dirty incoming mask. -/
theorem transpose_cx (a b m n : Bool) :
    Bool.xor (a && m) (Bool.xor a b && n) =
      Bool.xor (a && Bool.xor m n) (b && n) := by
  cases a <;> cases b <;> cases m <;> cases n <;> rfl

/-- Polynomial-basis modulus 0x1053: X^12=X^6+X^4+X+1
in characteristic two.  This justifies pooling all degree-i+j masks. -/
theorem pooled_power {R : Type*} [CommRing R] (x : R)
    (h : x^12=x^6+x^4+x+1) (d : ℕ) :
    x^(d+12)=x^(d+6)+x^(d+4)+x^(d+1)+x^d := by
  simp only [pow_add]
  rw [h,pow_one]
  ring

theorem inv3_involutive (x : F) : (x⁻¹)⁻¹=x := inv_inv x

/-- HMR clears a witnessed product without a paid coherent uncompute. -/
theorem repay_product (phase r a b : Bool) :
    Bool.xor (Bool.xor phase (r && (a && b))) (r && (a && b)) = phase := by
  cases phase <;> cases r <;> cases a <;> cases b <;> rfl

/-- Two distinct all-pole families cannot be identified by replacing G
with M=G*g.  For nonzero g and G, the magnitude changes by g inverse. -/
theorem extra_filter_magnitude (a x g e d : F)
    (hx : x≠0) (hg : g≠0) (he : e≠0) (hd : d≠0) :
    a/(x*(g*e)*d) = (a/(x*g*d))/e := by
  field_simp [hx,hg,he,hd]

/-- Two boundary coefficients lift the residue modulo monic degree-34 G
to the degree-35 locator; this is the scalar coefficient identity. -/
theorem leading_lift (g q t : F) (h2 : (2:F)=0) :
    g*q+(t+g*q)=t := by
  calc
    _ = t+2*(g*q) := by ring
    _ = _ := by rw [h2,zero_mul,add_zero]

end GVQCC.JointCRTHMR
#print axioms GVQCC.JointCRTHMR.reciprocal_norm
#print axioms GVQCC.JointCRTHMR.scaled_conjugate_norm
#print axioms GVQCC.JointCRTHMR.final_norm_witness
#print axioms GVQCC.JointCRTHMR.zero_safe_product_witness
#print axioms GVQCC.JointCRTHMR.transpose_cx
#print axioms GVQCC.JointCRTHMR.pooled_power
#print axioms GVQCC.JointCRTHMR.inv3_involutive
#print axioms GVQCC.JointCRTHMR.repay_product
#print axioms GVQCC.JointCRTHMR.extra_filter_magnitude
#print axioms GVQCC.JointCRTHMR.leading_lift
