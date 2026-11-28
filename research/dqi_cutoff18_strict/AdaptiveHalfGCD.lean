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
theorem binary_degree_step (d p : Nat) (h : d < 2*p) (_hp : 0 < p) :
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


namespace GVQCC.BalancedPade
open Polynomial
open scoped BigOperators

theorem precision_invariant (q v : Nat) (hv : v<q) :
    2*q-(v+(v+2)) = 2*(q-v-1) := by omega

theorem exact_history_width (q v : Nat) (hv : v<q) :
    (2*v+2)+2*(q-v-1)=2*q := by omega

theorem active_prefix (n i v : Nat) : i<n-v ↔ v<n-i := by omega

section Ring
variable {R : Type*} [CommRing R]

/-- One balanced block retires the valuation zeros, scalar and low inverse
    polynomial. The new quotient uses precisely the remaining precision. -/
theorem block_recover (a D N H P x : R) (v : Nat)
    (he : a*D=H*N+x^(v+2)*P) :
    a*(x^v*N)*D = (x^v*N)*(H*N+x^(v+2)*P) := by
  rw [← he]
  ring

theorem block_determinant (a H x : R) (v : Nat) :
    (-H)*0-(a*x^v)*x^(v+2) = -a*x^(2*v+2) := by
  rw [show 2*v+2=v+(v+2) by omega, pow_add]
  ring

theorem matrix_determinant_comp (a b c d e f g h : R) :
    (a*e+b*g)*(c*f+d*h)-(a*f+b*h)*(c*e+d*g) =
      (a*d-b*c)*(e*h-f*g) := by ring

theorem mobius_cross_difference (a b c d s t : R) :
    (a*(s+t)+b)*(c*s+d)-(a*s+b)*(c*(s+t)+d) =
      (a*d-b*c)*t := by ring

/-- Lift an already consumed prefix without copying the input series. -/
theorem packed_prefix_lift (a b c d s t A C x : R) (K : Nat)
    (ha : a*s+b=x^K*A) (hc : c*s+d=x^K*C) :
    a*(s+x^K*t)+b=x^K*(A+a*t) ∧
    c*(s+x^K*t)+d=x^K*(C+c*t) := by
  constructor
  · calc
      _ = (a*s+b)+x^K*(a*t) := by ring
      _ = _ := by rw [ha]; ring
  · calc
      _ = (c*s+d)+x^K*(c*t) := by ring
      _ = _ := by rw [hc]; ring

theorem prefix_adjoint (a b c d s A C x : R) (K : Nat)
    (ha : a*s+b=x^K*A) (hc : c*s+d=x^K*C) :
    x^K*(a*C-c*A)=a*d-b*c := by
  calc
    _ = a*(x^K*C)-c*(x^K*A) := by ring
    _ = _ := by rw [← hc, ← ha]; ring

theorem newton_double_char2 (f g e : R) (h2 : (2:R)=0)
    (h : f*g=1+e) :
    f*(f*g^2)=1+e^2 := by
  calc
    _ = (f*g)^2 := by ring
    _ = (1+e)^2 := by rw [h]
    _ = 1+e^2 := by
      calc
        _ = 1+e^2+2*e := by ring
        _ = _ := by rw [h2]; simp

/-- Source indices of Frobenius-power triangular update are lower than target. -/
theorem triangular_sources (i l k : Nat) (hl : 0<l) (hk : 2≤k)
    (h : k * l ≤ i) : l < i ∧ i-k*l < i := by
  have hm : 2 * l ≤ k * l := Nat.mul_le_mul_right l hk
  constructor <;> omega

theorem triangular_update_stable (s t : Nat → R) (i k : Nat)
    (hk : 2≤k) (L : Finset Nat)
    (hL : ∀ l ∈ L, 0 < l ∧ k * l ≤ i)
    (h : ∀ j < i, s j=t j) :
    (∑ l ∈ L, s (i - k * l)*(s l)^k) =
      ∑ l ∈ L, t (i - k * l)*(t l)^k := by
  apply Finset.sum_congr rfl
  intro l hl
  obtain ⟨h₁,h₂⟩ := hL l hl
  obtain ⟨h₃,h₄⟩ := triangular_sources i l k h₁ hk h₂
  rw [h _ h₃,h _ h₄]

/-- Contract measured outputs first, before applying the rank-one product.
    All independent measurement coefficients are retained. -/
theorem measured_output_dual {I J : Type*} [Fintype I] [Fintype J]
    (m : I → R) (w : J → I → R) (p : J → R) :
    (∑ i, m i*(∑ j, w j i*p j)) =
      ∑ j, p j*(∑ i, m i*w j i) := by
  simp_rw [Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro i _
  ring

end Ring

section Field
variable {F : Type*} [Field F]

/-- Degree of the new numerator, proved from the actual polynomial factorization
    rather than merely arithmetic on the asserted budgets. -/
theorem balanced_degree_bound (q v : Nat) (hv : v<q) (a : F)
    (D N H P : Polynomial F)
    (hd : D.natDegree≤q) (hn : N.natDegree≤q-v-1)
    (hh : H.natDegree≤v+1)
    (he : C a*D=H*N+X^(v+2)*P) :
    P=0 ∨ v+2+P.natDegree≤q := by
  by_cases hP : P=0
  · exact Or.inl hP
  right
  have hc : (C a*D).natDegree≤q := by
    calc
      _ ≤ (C a).natDegree+D.natDegree := natDegree_mul_le
      _ ≤ q := by simpa only [natDegree_C, zero_add] using hd
  have hm : (H*N).natDegree≤q := by
    calc
      _ ≤ H.natDegree+N.natDegree := natDegree_mul_le
      _ ≤ q := by omega
  have hx : X^(v+2)*P=C a*D-H*N := by rw [he]; ring
  have hp : (X^(v+2)*P).natDegree≤q := by
    rw [hx]
    exact le_trans (natDegree_sub_le _ _) (max_le hc hm)
  rw [natDegree_mul (pow_ne_zero _ X_ne_zero) hP, natDegree_X_pow] at hp
  exact hp

/-- Uniqueness of rational reconstruction on a balanced 2q-prefix. -/
theorem balanced_unique (q : Nat) (hq : 0<q)
    (N₁ D₁ N₂ D₂ : Polynomial F)
    (hn₁ : N₁.natDegree≤q-1) (hn₂ : N₂.natDegree≤q-1)
    (hd₁ : D₁.natDegree≤q) (hd₂ : D₂.natDegree≤q)
    (hdiv : X^(2*q) ∣ N₁*D₂-N₂*D₁) :
    N₁*D₂=N₂*D₁ := by
  obtain ⟨P,hP⟩ := hdiv
  have hm₁ : (N₁*D₂).natDegree≤2*q-1 := by
    calc
      _ ≤ N₁.natDegree+D₂.natDegree := natDegree_mul_le
      _ ≤ 2*q-1 := by omega
  have hm₂ : (N₂*D₁).natDegree≤2*q-1 := by
    calc
      _ ≤ N₂.natDegree+D₁.natDegree := natDegree_mul_le
      _ ≤ 2*q-1 := by omega
  have hd : (X^(2*q)*P).natDegree≤2*q-1 := by
    rw [← hP]
    exact le_trans (natDegree_sub_le _ _) (max_le hm₁ hm₂)
  by_cases hz : P=0
  · rw [hz, mul_zero] at hP
    exact sub_eq_zero.mp hP
  · rw [natDegree_mul (pow_ne_zero _ X_ne_zero) hz, natDegree_X_pow] at hd
    omega

end Field
end GVQCC.BalancedPade

#print axioms GVQCC.BalancedPade.precision_invariant
#print axioms GVQCC.BalancedPade.exact_history_width
#print axioms GVQCC.BalancedPade.active_prefix
#print axioms GVQCC.BalancedPade.block_recover
#print axioms GVQCC.BalancedPade.block_determinant
#print axioms GVQCC.BalancedPade.matrix_determinant_comp
#print axioms GVQCC.BalancedPade.mobius_cross_difference
#print axioms GVQCC.BalancedPade.packed_prefix_lift
#print axioms GVQCC.BalancedPade.prefix_adjoint
#print axioms GVQCC.BalancedPade.newton_double_char2
#print axioms GVQCC.BalancedPade.triangular_sources
#print axioms GVQCC.BalancedPade.triangular_update_stable
#print axioms GVQCC.BalancedPade.measured_output_dual
#print axioms GVQCC.BalancedPade.balanced_degree_bound
#print axioms GVQCC.BalancedPade.balanced_unique
