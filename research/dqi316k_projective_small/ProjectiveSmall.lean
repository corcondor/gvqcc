import Std

namespace GVQCC.ProjectiveSmall
variable {R : Type}

theorem shear_cancel (add : R → R → R) (zero : R)
    (ha : ∀ a b c, add (add a b) c = add a (add b c))
    (hz : ∀ a, add a a = zero)
    (hi : ∀ a, add a zero = a)
    (a b : R) : add (add a b) b = a := by
  rw [ha, hz, hi]

/-- Projective transport of a root residue. Here v is the common factor
    y^33 in the transformed derivative, and a=b*r is the old residue law. -/
theorem residue_transport (mul : R → R → R)
    (ha : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (a b r y v : R) (h : a = mul b r) :
    mul (mul y v) a = mul (mul y (mul v b)) r := by
  rw [h, ← ha (mul y v) b r, ha y v b]

/-- In the infinity chart D has degree 34. Multiply D by y, and
    replace N by y(N+qD)+qD, where q is the retired high coefficient.
    At every finite root of D, the extra terms vanish. -/
theorem padded_numerator_at_root (add mul : R → R → R) (zero : R)
    (hm : ∀ a, mul a zero = zero)
    (ha : ∀ a, add a zero = a)
    (d n q y : R) (hd : d = zero) :
    add (mul y (add n (mul q d))) (mul q d) = mul y n := by
  simp only [hd, hm, ha]

theorem padded_residue (mul : R → R → R)
    (ha : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (n d y r : R) (h : n = mul (mul y d) r) :
    mul y n = mul (mul y (mul y d)) r := by
  rw [h, ha]

/-- The retired quotient is stored in the new constant coefficient:
    c=q*d0. Its inverse is well-defined on the nonzero d0 chart. -/
theorem retired_quotient (mul : R → R → R) (one : R)
    (ha : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (hi : ∀ a, mul one a = a)
    (d0 di q c : R) (hu : mul di d0 = one) (hc : c = mul d0 q) :
    mul di c = q := by
  rw [hc, ← ha, hu, hi]

theorem chart_inverse {A : Type} (shift reverse : A → A)
    (hs : ∀ x, shift (shift x) = x)
    (hr : ∀ x, reverse (reverse x) = x) (x : A) :
    shift (reverse (reverse (shift x))) = x := by
  rw [hr, hs]

theorem zero_flag_repayment (f out m : Bool) (h : out = f) :
    Bool.xor (m && f) (m && out) = false := by
  subst out
  cases f <;> cases m <;> decide

theorem measured_width : 865 + 1 + 18 = 884 := by decide

#print axioms shear_cancel
#print axioms residue_transport
#print axioms padded_numerator_at_root
#print axioms padded_residue
#print axioms retired_quotient
#print axioms chart_inverse
#print axioms zero_flag_repayment
#print axioms measured_width
end GVQCC.ProjectiveSmall
