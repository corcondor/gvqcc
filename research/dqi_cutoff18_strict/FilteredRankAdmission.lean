import Mathlib

namespace GVQCC.FilteredRank

variable {V W : Type*} [AddCommGroup V] [AddCommGroup W]

/-- Padding is controlled only by a filter-invariant predicate. -/
def pad (F : V →+ W) (p : W → Bool) (g s : V) : V :=
  if p (F s) = true then s + g else s

theorem filter_shift (F : V →+ W) (g s : V) (hg : F g = 0) :
    F (s + g) = F s := by
  rw [map_add, hg, add_zero]

theorem predicate_invariant (F : V →+ W) (p : W → Bool)
    (g s : V) (hg : F g = 0) :
    p (F (s + g)) = p (F s) := by
  rw [filter_shift F g s hg]

theorem pad_preserves_filter (F : V →+ W) (p : W → Bool)
    (g s : V) (hg : F g = 0) :
    F (pad F p g s) = F s := by
  unfold pad
  split
  · exact filter_shift F g s hg
  · rfl

theorem pad_involution (F : V →+ W) (p : W → Bool)
    (g s : V) (hg : F g = 0) (h2 : g + g = 0) :
    pad F p g (pad F p g s) = s := by
  unfold pad
  by_cases h : p (F s) = true
  · have h' : p (F (s + g)) = true := by
      rw [filter_shift F g s hg]
      exact h
    rw [if_pos h, if_pos h', add_assoc, h2, add_zero]
  · simp only [if_neg h]

/-- A convolution with fixed coefficients rescales each geometric pole.
This is an algebraic lemma, not a native decoder correctness theorem. -/
theorem pole_filter {K : Type*} [Field K] (n i : ℕ)
    (c : Fin n → K) (a x : K) :
    (∑ j : Fin n, c j * (a * x ^ (i + j.val))) =
      (a * x ^ i) * (∑ j : Fin n, c j * x ^ j.val) := by
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro j _
  rw [pow_add]
  ring

/-- Conditional injectivity of the weighted moment map.
The Vandermonde hypothesis is explicit; it is not silently assumed proven. -/
theorem weighted_injective {K : Type*} [Field K] {r : ℕ}
    (x e v : Fin r → K)
    (hsep : ∀ b : Fin r → K,
      (∀ j : Fin r, ∑ k : Fin r, b k * x k ^ j.val = 0) → b = 0)
    (hnz : ∀ k, e k ≠ 0)
    (h : ∀ j : Fin r, ∑ k : Fin r, (e k * v k) * x k ^ j.val = 0) :
    v = 0 := by
  have h0 := hsep (fun k => e k * v k) h
  funext k
  have hh : e k * v k = 0 := congrFun h0 k
  exact (mul_eq_zero.mp hh).resolve_left (hnz k)

/-- No assumed Vandermonde separation: distinct poles suffice. -/
theorem weighted_injective_distinct {K : Type*} [Field K] {r : ℕ}
    (x e v : Fin r → K) (hx : Function.Injective x)
    (hnz : ∀ k, e k ≠ 0)
    (h : ∀ j : Fin r, ∑ k : Fin r, (e k * v k) * x k ^ j.val = 0) :
    v = 0 := by
  apply weighted_injective x e v _ hnz h
  intro b hb
  exact Matrix.eq_zero_of_forall_pow_sum_mul_pow_eq_zero hx hb

/-- The residual detects missing true poles even when the candidate has
extra/repeated roots. v k represents its evaluation at the true pole k. -/
theorem residual_zero_iff {K : Type*} [Field K] {r : ℕ}
    (x e v : Fin r → K) (hx : Function.Injective x)
    (hnz : ∀ k, e k ≠ 0) :
    (∀ j : Fin r, ∑ k : Fin r, (e k * v k) * x k ^ j.val = 0) ↔ v = 0 := by
  constructor
  · exact weighted_injective_distinct x e v hx hnz
  · intro h
    subst v
    simp

/-- Two coefficient vectors on a common set of at most 70 distinct poles
with equal moments must coincide (apply to the union of two supports). -/
theorem distinct_moments_injective {K : Type*} [Field K] {r : ℕ}
    (x a b : Fin r → K) (hx : Function.Injective x)
    (h : ∀ j : Fin r, ∑ k : Fin r, a k * x k ^ j.val =
        ∑ k : Fin r, b k * x k ^ j.val) :
    a = b := by
  have hzero : ∀ j : Fin r, ∑ k : Fin r, (a k - b k) * x k ^ j.val = 0 := by
    intro j
    simp_rw [sub_mul, Finset.sum_sub_distrib]
    exact sub_eq_zero.mpr (h j)
  have hz : (fun k => a k - b k) = 0 :=
    Matrix.eq_zero_of_forall_pow_sum_mul_pow_eq_zero hx hzero
  funext k
  exact sub_eq_zero.mp (congrFun hz k)

theorem padded_degree_bound (w : ℕ) (h : w < 18) :
    w + 18 ≤ 35 := by omega

/-- More selected zero-cost leaves cannot raise the modeled leaf cost.
No assertion of full-circuit phase equivalence is made here. -/
theorem leaf_cost_nonincrease (n old candidate : ℕ) :
    11 * (n - max old candidate) ≤ 11 * (n - old) := by
  have h : old ≤ max old candidate := le_max_left _ _
  omega

/-- The HMR repayment sign is bilinear over Bool. -/
theorem repayment_split (m a b : Bool) :
    (m && (a ^^ b)) = ((m && a) ^^ (m && b)) := by
  cases m <;> cases a <;> cases b <;> decide

#print axioms filter_shift
#print axioms predicate_invariant
#print axioms pad_preserves_filter
#print axioms pad_involution
#print axioms pole_filter
#print axioms weighted_injective
#print axioms weighted_injective_distinct
#print axioms residual_zero_iff
#print axioms distinct_moments_injective
#print axioms padded_degree_bound
#print axioms leaf_cost_nonincrease
#print axioms repayment_split

end GVQCC.FilteredRank


namespace GVQCC.ExactHankel

variable {K : Type*} [Field K]

/-- Moments are indexed from zero; for S_(i+1) use w_k = e_k*x_k. -/
def hankel {r : ℕ} (n : ℕ) (x w : Fin r → K) : Matrix (Fin n) (Fin n) K :=
  Matrix.of fun i j => ∑ k : Fin r, w k * x k ^ (i.val + j.val)

def vanderRect {r : ℕ} (n : ℕ) (x : Fin r → K) : Matrix (Fin n) (Fin r) K :=
  Matrix.of fun i k => x k ^ i.val

theorem hankel_factor {r : ℕ} (n : ℕ) (x w : Fin r → K) :
    hankel n x w = (vanderRect n x * Matrix.diagonal w) * (vanderRect n x).transpose := by
  classical
  ext i j
  rw [Matrix.mul_apply]
  simp only [hankel, Matrix.of_apply, Matrix.mul_diagonal, Matrix.transpose_apply, vanderRect, pow_add]
  apply Finset.sum_congr rfl
  intro k _
  ring

/-- The leading square minor is nonsingular, even in characteristic two. -/
theorem hankel_det {r : ℕ} (x w : Fin r → K)
    (hx : Function.Injective x) (hw : ∀ k, w k ≠ 0) :
    (hankel r x w).det ≠ 0 := by
  classical
  have hv : vanderRect r x = (Matrix.vandermonde x).transpose := rfl
  have hd : (Matrix.vandermonde x).det ≠ 0 :=
    Matrix.det_vandermonde_ne_zero_iff.mpr hx
  have hp : (∏ k : Fin r, w k) ≠ 0 :=
    Finset.prod_ne_zero_iff.mpr (by intro k _; exact hw k)
  rw [hankel_factor, hv]
  simp only [Matrix.det_mul, Matrix.det_transpose, Matrix.det_diagonal]
  exact mul_ne_zero (mul_ne_zero hd hp) hd

/-- Exact rank, not an assumed Vandermonde separation or a sampled rank.
For a legal DQI support of r distinct nonzero poles with nonzero amplitudes,
take n=35 and w_k=e_k*x_k. Covers r=0 and every singular r<35. -/
theorem hankel_rank_eq_weight {n r : ℕ} (hr : r ≤ n) (x w : Fin r → K)
    (hx : Function.Injective x) (hw : ∀ k, w k ≠ 0) :
    (hankel n x w).rank = r := by
  classical
  have hu : (hankel n x w).rank ≤ r := by
    rw [hankel_factor]
    exact (Matrix.rank_mul_le_left _ _).trans
      ((Matrix.rank_mul_le_left _ _).trans (Matrix.rank_le_width _))
  let incl : Fin r → Fin n := fun i => ⟨i.val, lt_of_lt_of_le i.isLt hr⟩
  have hm : (hankel r x w).rank = r := by
    simpa using Matrix.rank_of_det_ne_zero (hankel_det x w hx hw)
  have hl := Matrix.rank_submatrix_le (hankel n x w) incl incl
  change (hankel r x w).rank ≤ (hankel n x w).rank at hl
  omega

/-- Actual residual moment sequence on n rows. -/
def poleResidual {r : ℕ} (n : ℕ) (x w v : Fin r → K) : Fin n → K :=
  fun i => ∑ k : Fin r, (w k * v k) * x k ^ i.val

theorem poleResidual_zero_iff {n r : ℕ} (hr : r ≤ n) (x w v : Fin r → K)
    (hx : Function.Injective x) (hw : ∀ k, w k ≠ 0) :
    (∀ i, poleResidual n x w v i = 0) ↔ v = 0 := by
  constructor
  · intro h
    let incl : Fin r → Fin n := fun i => ⟨i.val, lt_of_lt_of_le i.isLt hr⟩
    have hz : (fun k => w k * v k) = 0 :=
      Matrix.eq_zero_of_forall_pow_sum_mul_pow_eq_zero hx (fun j => h (incl j))
    funext k
    have hk : w k * v k = 0 := congrFun hz k
    exact (mul_eq_zero.mp hk).resolve_left (hw k)
  · intro h
    subst v
    simp [poleResidual]

/-- Connect the residual test to the actual Hankel matrix-vector product. -/
theorem hankel_mulVec_eval {n r : ℕ} (x w : Fin r → K) (p : Fin n → K) (i : Fin n) :
    (hankel n x w).mulVec p i =
      poleResidual n x w (fun k => ∑ j : Fin n, p j * x k ^ j.val) i := by
  classical
  simp only [Matrix.mulVec, dotProduct, hankel, Matrix.of_apply, poleResidual, pow_add,
    Finset.sum_mul, Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro k _
  apply Finset.sum_congr rfl
  intro j _
  ring

/-- The true syndrome residual of a monic degree-n locator, not just a
free abstract evaluation vector. No squarefree assumption on the candidate. -/
theorem candidate_residual_formula {n r : ℕ} (x w : Fin r → K)
    (p : Fin n → K) (i : Fin n) :
    (hankel n x w).mulVec p i + (∑ k : Fin r, w k * x k ^ (i.val + n)) =
      poleResidual n x w (fun k => (∑ j : Fin n, p j * x k ^ j.val) + x k ^ n) i := by
  rw [hankel_mulVec_eval]
  simp only [poleResidual, pow_add, mul_add, add_mul, Finset.sum_add_distrib]
  congr 1
  apply Finset.sum_congr rfl
  intro k _
  ring

theorem candidate_residual_iff {n r : ℕ} (hr : r ≤ n) (x w : Fin r → K)
    (p : Fin n → K) (hx : Function.Injective x) (hw : ∀ k, w k ≠ 0) :
    (∀ i : Fin n, (hankel n x w).mulVec p i +
       (∑ k : Fin r, w k * x k ^ (i.val + n)) = 0) ↔
    (∀ k : Fin r, (∑ j : Fin n, p j * x k ^ j.val) + x k ^ n = 0) := by
  simp_rw [candidate_residual_formula]
  rw [poleResidual_zero_iff hr x w _ hx hw]
  constructor
  · intro h k
    exact congrFun h k
  · intro h
    funext k
    exact h k

#print axioms hankel_factor
#print axioms hankel_det
#print axioms hankel_rank_eq_weight
#print axioms poleResidual_zero_iff
#print axioms hankel_mulVec_eval
#print axioms candidate_residual_formula
#print axioms candidate_residual_iff

end GVQCC.ExactHankel
