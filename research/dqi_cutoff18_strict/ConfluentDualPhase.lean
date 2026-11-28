import Mathlib

namespace GVQCC.ConfluentDualPhase
open scoped BigOperators

section Pairing
variable {R I : Type*} [CommRing R] [Fintype I]

def pairing (x y : I → R) : R := ∑ i, x i * y i
def act (L : I → I → R) (x : I → R) : I → R :=
  fun i => ∑ j, L i j * x j
def tr (L : I → I → R) : I → I → R := fun i j => L j i

theorem adjoint (L : I → I → R) (x z : I → R) :
    pairing (act L x) z = pairing x (act (tr L) z) := by
  simp only [pairing, act, tr, Finset.sum_mul, Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro i _
  ring

/-- The inverse triangular map is specified by its exact equations;
    the phase identity needs no construction of the original inverse matrix. -/
theorem transported_pairing (L : I → I → R) (m h z w : I → R)
    (hm : act L h = m) (hw : act (tr L) z = w) :
    pairing m z = pairing h w := by
  rw [← hm, adjoint, hw]
end Pairing

section TruncatedRing
variable {R : Type*} [CommRing R]

/-- Valid in the truncated polynomial ring R[X]/(X^r).
    Cancel a denominator rather than solve the anti-Hankel matrix. -/
theorem quotient_cancel (A V gamma f e z u : R)
    (hgamma : gamma * V = A) (he : V * e = f)
    (hz : A * z = f) (hu : V * u = 1) : gamma * z = e := by
  calc
    gamma * z = (gamma * z) * (V * u) := by rw [hu, mul_one]
    _ = (gamma * V) * z * u := by ring
    _ = f * u := by rw [hgamma, hz]
    _ = (V * e) * u := by rw [he]
    _ = e * (V * u) := by ring
    _ = e := by rw [hu, mul_one]

theorem direct_product (A V f m z h ai vi : R)
    (hf : z = f * ai) (hm : h = m * vi)
    (ha : A * ai = 1) (hv : V * vi = 1) :
    (A * V) * (z * h) = f * m := by
  rw [hf, hm]
  calc
    _ = f * m * (A * ai) * (V * vi) := by ring
    _ = f * m := by rw [ha, hv, mul_one, mul_one]

theorem arbitrary_order_numerator (x y j k v w g h : R) (r : ℕ) :
    (x^r*j+g*v)*(y^r*w)+(y^r*k+h*w)*(x^r*v)=
      x^r*y^r*(j*w+k*v)+v*w*(g*y^r+h*x^r) := by ring

theorem square_add_char2 (a b : R) (h2 : (2:R)=0) :
    (a+b)^2=a^2+b^2 := by
  calc
    _ = a^2+b^2+2*(a*b) := by ring
    _ = _ := by rw [h2,zero_mul,add_zero]

theorem nilpotent_projector_step (a : R) (k : ℕ) (h2 : (2:R)=0)
    (ha : a^(2^k)=0) : (1+a)^(2^k)=1 := by
  have h : ∀ n : ℕ, (1+a)^(2^n)=1+a^(2^n) := by
    intro n
    induction n with
    | zero => simp
    | succ n ih =>
      rw [pow_succ (2:ℕ) n, pow_mul, ih, square_add_char2 _ _ h2, one_pow, ← pow_mul]
  rw [h,ha,add_zero]
end TruncatedRing

section Toeplitz
variable {R : Type*} [Zero R]

def flip {r : ℕ} (j : Fin r) : Fin r := ⟨r-1-j.val, by omega⟩
def lower {r : ℕ} (a : ℕ → R) (i j : Fin r) : R :=
  if j.val ≤ i.val then a (i.val-j.val) else 0

/-- Reversing the column index turns the lower Toeplitz matrix into
    the anti-triangular Hankel matrix of Bezout(gamma, X^r). -/
theorem anti_hankel_factor {r : ℕ} (a : ℕ → R) (i j : Fin r) :
    lower a i (flip j) =
      if r-1 ≤ i.val+j.val then a (i.val+j.val-(r-1)) else 0 := by
  unfold lower flip
  dsimp
  by_cases h : r-1 ≤ i.val+j.val
  · have h' : r-1-j.val ≤ i.val := by omega
    rw [if_pos h,if_pos h']
    congr 1
    omega
  · have h' : ¬ r-1-j.val ≤ i.val := by omega
    rw [if_neg h,if_neg h']
end Toeplitz

theorem hmr_product_debt (a b m : Bool) :
    Bool.xor (m && (a && b)) ((m && a) && b) = false := by
  cases a <;> cases b <;> cases m <;> decide

#print axioms adjoint
#print axioms transported_pairing
#print axioms quotient_cancel
#print axioms direct_product
#print axioms arbitrary_order_numerator
#print axioms square_add_char2
#print axioms nilpotent_projector_step
#print axioms anti_hankel_factor
#print axioms hmr_product_debt
end GVQCC.ConfluentDualPhase
