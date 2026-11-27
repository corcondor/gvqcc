import Mathlib

namespace GVQCC.InfinityCF

/-- A selector that is stable under its selected involution need not be saved. -/
def selected {A : Type*} (tag : A → ℕ) (T : ℕ → A → A) (x : A) : A :=
  T (tag x) x

theorem selected_involutive {A : Type*} (tag : A → ℕ) (T : ℕ → A → A)
    (hi : ∀ n, Function.Involutive (T n))
    (hs : ∀ x, tag (T (tag x) x) = tag x) :
    Function.Involutive (selected tag T) := by
  intro x
  unfold selected
  rw [hs x]
  exact hi (tag x) x

/-- Fixed list of locally invertible steps; inverse runs in reverse order.
The lists are public circuit schedules, not a stored input-dependent history. -/
def run {A : Type*} : List (A → A) → A → A
  | [], x => x
  | f::fs, x => run fs (f x)

def undo {A : Type*} : List (A → A) → A → A
  | [], x => x
  | f::fs, x => f (undo fs x)

theorem undo_run {A : Type*} (fs : List (A → A))
    (hf : ∀ f ∈ fs, Function.Involutive f) (x : A) :
    undo fs (run fs x) = x := by
  induction fs generalizing x with
  | nil => rfl
  | cons f fs ih =>
    have htail : ∀ g ∈ fs, Function.Involutive g := by
      intro g hg
      exact hf g (List.mem_cons_of_mem f hg)
    change f (undo fs (run fs (f x))) = x
    rw [ih htail]
    exact hf f (by simp) x

theorem selected_injective {A : Type*} (tag : A → ℕ) (T : ℕ → A → A)
    (hi : ∀ n, Function.Involutive (T n))
    (hs : ∀ x, tag (T (tag x) x) = tag x) :
    Function.Injective (selected tag T) :=
  (selected_involutive tag T hi hs).injective

/-- With a degree drop d the precision 2w suffices after removing 2d words. -/
theorem precision_budget (L w d : ℕ) (hL : 2*w ≤ L) (hd : d ≤ w) :
    2*(w-d) ≤ L-2*d := by omega

theorem exact_block_length (d : ℕ) (hd : 0 < d) :
    d-1+(d+1)=2*d := by omega

theorem degree_word_budget (ds : List ℕ) :
    (ds.map (fun d => 2*d)).sum = 2*ds.sum := by
  induction ds with
  | nil => simp
  | cons d ds ih => simp [ih, Nat.mul_add]

theorem physical_budget (ds : List ℕ) (h : ds.sum ≤ 35) :
    12*(ds.map (fun d => 2*d)).sum ≤ 840 := by
  rw [degree_word_budget]
  omega

/-- Uniqueness of reciprocals in a commutative ring. In particular it
applies in the quotient by the chosen truncation ideal. -/
theorem reciprocal_unique {R : Type*} [CommRing R] (a b c : R)
    (hb : a*b=1) (hc : a*c=1) : b=c := by
  calc
    b = b*(a*c) := by rw [hc, mul_one]
    _ = (a*b)*c := by ring
    _ = c := by rw [hb, one_mul]

theorem euclid_step_inverse {R : Type*} [CommRing R] (n d q r : R)
    (h : d=q*n+r) : q*n+r=d := h.symm

theorem euclid_bezout {R : Type*} [CommRing R] (n d q r : R)
    (h : d=q*n+r) (hb : ∃ a b : R, a*n+b*d=1) :
    ∃ a b : R, a*r+b*n=1 := by
  obtain ⟨a,b,hab⟩ := hb
  rw [h] at hab
  refine ⟨b,a+b*q,?_⟩
  linear_combination hab

open Polynomial

theorem euclid_degree {F : Type*} [Field F]
    (n d q r : Polynomial F) (hn : n ≠ 0) (hq : q ≠ 0)
    (h : d=q*n+r) (hr : r=0 ∨ r.natDegree<n.natDegree) :
    d.natDegree=q.natDegree+n.natDegree := by
  rcases hr with hr | hr
  · rw [h, hr, add_zero, Polynomial.natDegree_mul hq hn]
  · have hh : r.natDegree < (q*n).natDegree := by
      rw [Polynomial.natDegree_mul hq hn]
      omega
    rw [h, Polynomial.natDegree_add_eq_left_of_natDegree_lt hh,
      Polynomial.natDegree_mul hq hn]

/-- Unit-series elimination and reconstruction are triangular field shears. -/
theorem char_two_shear {R : Type*} [CommRing R] (x a b : R)
    (h : (2:R)=0) : (x+a*b)+a*b=x := by
  calc
    _ = x+2*(a*b) := by ring
    _ = x := by rw [h,zero_mul,add_zero]

theorem square_linear {R : Type*} [CommRing R] (a b : R)
    (h : (2:R)=0) : (a+b)^2=a^2+b^2 := by
  calc
    _ = a^2+b^2+2*a*b := by ring
    _ = _ := by rw [h,zero_mul,zero_mul,add_zero]

/-- Leading coefficient inversion preserves the zero pattern used to parse
the first word of the block. -/
theorem inv_head_zero_iff {F : Type*} [Field F] (a : F) : a⁻¹=0 ↔ a=0 := inv_eq_zero

end GVQCC.InfinityCF

#print axioms GVQCC.InfinityCF.selected_involutive
#print axioms GVQCC.InfinityCF.undo_run
#print axioms GVQCC.InfinityCF.selected_injective
#print axioms GVQCC.InfinityCF.precision_budget
#print axioms GVQCC.InfinityCF.exact_block_length
#print axioms GVQCC.InfinityCF.degree_word_budget
#print axioms GVQCC.InfinityCF.physical_budget
#print axioms GVQCC.InfinityCF.reciprocal_unique
#print axioms GVQCC.InfinityCF.euclid_step_inverse
#print axioms GVQCC.InfinityCF.euclid_bezout
#print axioms GVQCC.InfinityCF.euclid_degree
#print axioms GVQCC.InfinityCF.char_two_shear
#print axioms GVQCC.InfinityCF.square_linear
#print axioms GVQCC.InfinityCF.inv_head_zero_iff
