import Mathlib

namespace GVQCC.SafeDegreeGauge
variable {K : Type*} [Field K]

/-- Exactly the available nonconstant raw moments S1,...,Sn. -/
def moment {r : ℕ} (x e : Fin r → K) (j : ℕ) : K :=
  ∑ k : Fin r, e k * x k ^ (j + 1)

def evalGauge {n : ℕ} (c : Fin n → K) (t : K) : K :=
  ∑ j : Fin n, c j * t ^ (j.val + 1)

/-- Pair the polynomial with the raw input rather than a reconstructed locator. -/
theorem gauge_pairing {r n : ℕ} (x e : Fin r → K) (c : Fin n → K) :
    (∑ k : Fin r, e k * evalGauge c (x k)) =
    ∑ j : Fin n, c j * moment x e j.val := by
  classical
  simp only [evalGauge, moment, Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro k _
  ring

/-- The gauge may be ANY function of public masks. No locator correctness,
S71, distinct-root, or nonsingularity assumption enters this identity. -/
theorem repay_all {r n : ℕ} (x e m : Fin r → K) (c : Fin n → K)
    (h2 : ∀ a : K, a + a = 0) :
    (∑ k : Fin r, e k * (m k + evalGauge c (x k))) +
      (∑ j : Fin n, c j * moment x e j.val) =
    ∑ k : Fin r, e k * m k := by
  simp_rw [mul_add, Finset.sum_add_distrib]
  rw [gauge_pairing, add_assoc, h2, add_zero]

/-- Strict public acceptance or rejection has identical intended phase. -/
theorem selected_gauge {r n : ℕ} (x e m : Fin r → K) (c : Fin n → K)
    (h2 : ∀ a : K, a + a = 0) (use : Bool) :
    (∑ k : Fin r, e k * (if use then m k + evalGauge c (x k) else m k)) +
      (if use then ∑ j : Fin n, c j * moment x e j.val else 0) =
    ∑ k : Fin r, e k * m k := by
  cases use
  · simp
  · simpa using repay_all x e m c h2

theorem mask_restore (a b : K) (h2 : ∀ t : K, t + t = 0) :
    a + b + b = a := by rw [add_assoc, h2, add_zero]

theorem leading_cancel (p q : K) (hp : p ≠ 0) (h2 : ∀ t : K, t + t = 0) :
    q + (q / p) * p = 0 := by
  have h : (q / p) * p = q := (div_eq_iff hp).mp rfl
  rw [h, h2]

theorem zero_leaf (e : K) : e * 0 = 0 := mul_zero e

/-- If the entire public mask lies in the known-moment span, the arithmetic
decoder is unnecessary, even on a singular or previously failing input. -/
theorem full_mask_bypass {r n : ℕ} (x e m : Fin r → K) (c : Fin n → K)
    (hm : ∀ k, m k = evalGauge c (x k)) :
    (∑ k : Fin r, e k * m k) = ∑ j : Fin n, c j * moment x e j.val := by
  have h : m = fun k => evalGauge c (x k) := funext hm
  rw [h]
  exact gauge_pairing x e c

theorem support_admission (n oldZero newZero : ℕ) (h : oldZero ≤ newZero) :
    n - newZero ≤ n - oldZero := Nat.sub_le_sub_left h n

theorem bypass_paid_nonincrease (paid : ℕ) (use : Bool) :
    (if use then 0 else paid) ≤ paid := by cases use <;> simp

#print axioms gauge_pairing
#print axioms repay_all
#print axioms selected_gauge
#print axioms mask_restore
#print axioms leading_cancel
#print axioms zero_leaf
#print axioms full_mask_bypass
#print axioms support_admission
#print axioms bypass_paid_nonincrease

end GVQCC.SafeDegreeGauge
