import Mathlib

namespace GVQCC.GuardedPhase316
open scoped BigOperators

/-- Exact binary coefficients of the five-point GF(4) interpolation
tensor used by joint_rank15.py, in the GF(64) polynomial basis. -/
def terms : List (Nat × Nat × Nat) :=
  [(25,25,42),(56,56,9),(33,33,35),
   (23,23,13),(32,32,14),(55,55,3),
   (29,29,34),(30,30,16),(3,3,50),
   (19,19,62),(6,6,22),(21,21,40),
   (28,28,23),(48,48,18),(44,44,5)]

def tensorAt (i j : Nat) : Nat :=
  terms.foldl (fun a t => if t.1.testBit i && t.2.1.testBit j
    then Nat.xor a t.2.2 else a) 0

/-- X^n in GF(2)[X]/(X^6+X+1). -/
def monomial : Nat → Nat
  | 0 => 1
  | n+1 => let r := monomial n
           if r ≥ 32 then Nat.xor (2*r) 67 else 2*r

theorem tensor_count : terms.length = 15 := rfl

theorem tensor_basis : ∀ i j : Fin 6,
    tensorAt i.val j.val = monomial (i.val+j.val) := by decide

/-- Bilinear maps agree on every vector if their basis coefficients agree. -/
theorem bilinear_basis_complete {R : Type*} [Semiring R]
    (a b : Fin 6 → R) (A B : Fin 6 → Fin 6 → R)
    (h : ∀ i j, A i j = B i j) :
    (∑ i, ∑ j, a i * b j * A i j) =
    (∑ i, ∑ j, a i * b j * B i j) := by
  simp_rw [h]

variable {F : Type*} [Field F]

/-- The two nested norm calculations use the same conjugation law. -/
theorem norm_product (a b k beta : F) (hb : beta^2=beta+k)
    (h2 : (2:F)=0) :
    (a+b*beta)*((a+b)+b*beta)=a^2+a*b+k*b^2 := by
  linear_combination b^2*hb + (a*b*beta+b^2*beta)*h2

/-- Valid at zero as well, given the irreducible-extension norm condition. -/
theorem inverse_from_norm (z c n : F) (hprod : z*c=n)
    (hz : n=0 → z=0) : c*n⁻¹=z⁻¹ := by
  by_cases hn : n=0
  · simp [hn,hz hn]
  · have hzz : z≠0 := by
      intro h
      apply hn
      simpa [h] using hprod.symm
    have hzc : z*(c*n⁻¹)=1 := by
      rw [← mul_assoc,hprod,mul_inv_cancel₀ hn]
    calc
      c*n⁻¹ = z⁻¹*(z*(c*n⁻¹)) := by
        rw [← mul_assoc,inv_mul_cancel₀ hzz,one_mul]
      _ = z⁻¹ := by rw [hzc,mul_one]

/-- Place the root and chart guard on the three-bit inner inverse,
rather than on each of the twelve output bits. -/
theorem nested_gated_inverse (z c n d m : F)
    (h1 : z*c=n) (h2 : n*d=m)
    (hz : n=0 → z=0) (hn : m=0 → n=0) (active : Bool) :
    c*(d*(if active then m⁻¹ else 0)) =
      (if active then z⁻¹ else 0) := by
  cases active
  · simp
  · simp only [ite_true]
    rw [inverse_from_norm n d m h2 hn,inverse_from_norm z c n h1 hz]

/-- Rolling Chien evaluation preserves each coefficient contribution. -/
theorem rolling_eval (a x alpha : F) (j : Nat) :
    (a*x^j)*alpha^j = a*(x*alpha)^j := by
  rw [mul_pow]
  ring

/-- A derivative term multiplied by x is in the same rolling frame. -/
theorem derivative_term (a x : F) (n : Nat) :
    x*((n:F)*a*x^(n-1))=(n:F)*a*x^n := by
  cases n with
  | zero => simp
  | succ k =>
    simp only [Nat.succ_sub_one,pow_succ]
    ring

theorem derivative_even (n : Nat) (h2 : (2:F)=0) :
    ((2*n:Nat):F)=0 := by
  rw [Nat.cast_mul,Nat.cast_ofNat,h2,zero_mul]

theorem derivative_odd (n : Nat) (h2 : (2:F)=0) :
    ((2*n+1:Nat):F)=1 := by
  rw [Nat.cast_add,Nat.cast_mul,Nat.cast_ofNat,h2,zero_mul,Nat.cast_one,zero_add]

/-- Constant inverse G(x) can be moved to the classical mask. -/
theorem inverse_factor (g d : F) (hg : g≠0) (hd : d≠0) :
    (g*d)⁻¹=g⁻¹*d⁻¹ := by
  field_simp [hg,hd]

theorem transpose_mask {R : Type*} [CommSemiring R]
    {I J : Type*} [Fintype I] [Fintype J]
    (A : J → I → R) (v : I → R) (m : J → R) :
    (∑ j, m j*(∑ i, A j i*v i)) =
      ∑ i, (∑ j, A j i*m j)*v i := by
  simp_rw [Finset.mul_sum,Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro i _
  apply Finset.sum_congr rfl
  intro j _
  ac_rfl

end GVQCC.GuardedPhase316
#print axioms GVQCC.GuardedPhase316.tensor_count
#print axioms GVQCC.GuardedPhase316.tensor_basis
#print axioms GVQCC.GuardedPhase316.bilinear_basis_complete
#print axioms GVQCC.GuardedPhase316.norm_product
#print axioms GVQCC.GuardedPhase316.inverse_from_norm
#print axioms GVQCC.GuardedPhase316.nested_gated_inverse
#print axioms GVQCC.GuardedPhase316.rolling_eval
#print axioms GVQCC.GuardedPhase316.derivative_term
#print axioms GVQCC.GuardedPhase316.derivative_even
#print axioms GVQCC.GuardedPhase316.derivative_odd
#print axioms GVQCC.GuardedPhase316.inverse_factor
#print axioms GVQCC.GuardedPhase316.transpose_mask
