import Mathlib

namespace GVQCC.ProjectivePivot316

variable {F : Type*} [Field F] [DecidableEq F]

/-- Total residue permutation. Axes are exchanged; on the torus the
second coordinate is scaled by the inverse of the first. -/
def pivot (n d : F) : F × F :=
  if n = 0 ∨ d = 0 then (d,n) else (n,d/n)

def unpivot (p h : F) : F × F :=
  if p = 0 ∨ h = 0 then (h,p) else (p,h*p)

theorem unpivot_pivot (n d : F) :
    unpivot (pivot n d).1 (pivot n d).2 = (n,d) := by
  by_cases hn : n = 0
  · subst n
    simp [pivot,unpivot]
  · by_cases hd : d = 0
    · subst d
      simp [pivot,unpivot]
    · have hh : d/n ≠ 0 := div_ne_zero hd hn
      simp [pivot,unpivot,hn,hd,hh,div_mul_cancel₀ d hn]

theorem pivot_unpivot (p h : F) :
    pivot (unpivot p h).1 (unpivot p h).2 = (p,h) := by
  by_cases hp : p = 0
  · subst p
    simp [pivot,unpivot]
  · by_cases hh : h = 0
    · subst h
      simp [pivot,unpivot]
    · have hd : h*p ≠ 0 := mul_ne_zero hh hp
      simp [pivot,unpivot,hp,hh,hd,mul_div_cancel_right₀ h hp]

/-- Only when the incoming denominator is a unit does the zero
quotient distinguish a singular numerator without another tag. -/
theorem sentinel (n d : F) (hd : d ≠ 0) :
    (pivot n d).1 ≠ 0 ∧ ((pivot n d).2 = 0 ↔ n = 0) := by
  by_cases hn : n = 0
  · subst n
    simp [pivot,hd]
  · have hh : d/n ≠ 0 := div_ne_zero hd hn
    simp [pivot,hn,hd,hh]

/- The missing flag cannot be dropped when the denominator is zero.
Both axes produce the same output of the old zero-safe ratio formula. -/
omit [DecidableEq F] in
theorem old_ratio_collision (d : F) (hd : d ≠ 0) :
    (d, (0:F)/d) = (d, d/(0:F)) ∧ ((d, (0:F)) ≠ (0,d)) := by
  constructor
  · simp
  · intro h
    exact hd (congrArg Prod.fst h)

section PolynomialStep
variable {R : Type*} [CommRing R] [DecidableEq R]

/-- Recover the polynomial pair from its reduced chart and stored h.
In the singular branch h=0, divide the numerator; otherwise divide
D+hN and exchange the roles of the reduced pair. -/
def recover (g h a b : R) : R × R :=
  if h = 0 then (g*a,b) else (b,g*a-h*b)

theorem regular_recover (g h a n d : R) (hh : h ≠ 0)
    (he : d+h*n=g*a) : recover g h a n = (n,d) := by
  have he' : g*a-h*n=d := by rw [←he,add_sub_cancel_right]
  simp [recover,hh,he']

theorem singular_recover (g a n d : R) (he : n=g*a) :
    recover g 0 a d = (n,d) := by simp [recover,he]

/- In either admissible chart the new denominator remains nonzero
under the SAME residue evaluation. This justifies the zero sentinel
on repeated nodes, not on an arbitrary next distinct node. -/
omit [DecidableEq R] in
theorem repeated_denominator (ev : R →+* F) (n d : R)
    (hd : ev d ≠ 0) :
    ev (if ev n = 0 then d else n) ≠ 0 := by
  by_cases hn : ev n = 0
  · simp [hn,hd]
  · simp [hn]

/- If N and D are coprime, both residues cannot be zero. -/
omit [DecidableEq R] [DecidableEq F] in
theorem not_both_zero (ev : R →+* F) (n d : R)
    (h : ∃ a b : R, a*n+b*d=1) :
    ¬ (ev n=0 ∧ ev d=0) := by
  rintro ⟨hn,hd⟩
  obtain ⟨a,b,hab⟩ := h
  have he := congrArg ev hab
  simp [hn,hd] at he

/- Division after the ordinary chart shear preserves the Bezout witness. -/
omit [DecidableEq R] in
theorem bezout_regular (g h q n d : R)
    (he : d+h*n=g*q) (hc : ∃ a b : R, a*n+b*d=1) :
    ∃ a b : R, a*n+b*q=1 := by
  obtain ⟨a,b,hab⟩ := hc
  refine ⟨a-b*h,b*g,?_⟩
  linear_combination hab - b*he

/- Exact division on a singular axis preserves the Bezout witness. -/
omit [DecidableEq R] in
theorem bezout_singular (g q n d : R)
    (he : n=g*q) (hc : ∃ a b : R, a*n+b*d=1) :
    ∃ a b : R, a*q+b*d=1 := by
  obtain ⟨a,b,hab⟩ := hc
  refine ⟨a*g,b,?_⟩
  linear_combination hab - a*he

end PolynomialStep

/-- With degree scheduling, a regular polynomial reduction by a
monic quadratic decreases the larger length by at least two unless
the input lengths tie. In the tie case a one-word drop suffices.
This arithmetic lemma bounds the potential independently of the
physical placement of the stored quotient and orientation. -/
theorem length_potential (a b q : ℕ) (h : q < a)
    (h₂ : a ≠ b → q+2 ≤ a) :
    (q+b)/2 < (a+b)/2 := by
  by_cases hab : a = b
  · subst b
    omega
  · have hd := h₂ hab
    omega

theorem degree_schedule_length (a b q h : ℕ) (_ha : 0<a)
    (hb : b ≤ a) (hh : h ≤ 2)
    (hq : q+2 ≤ max a (b+h-1)) :
    q < a ∧ (a≠b → q+2≤a) := by omega

theorem potential_budget (p : ℕ → ℕ) (k : ℕ)
    (h : ∀ i < k, p (i+1) < p i) : p k+k ≤ p 0 := by
  induction k with
  | zero => simp
  | succ k ih =>
    have hp := ih (fun i hi => h i (by omega))
    have hk := h k (by omega)
    omega

theorem thirtyfive_bound (p : ℕ → ℕ) (k : ℕ)
    (h0 : p 0 ≤ 35) (h : ∀ i < k, p (i+1) < p i) : k ≤ 35 := by
  have h₁ := potential_budget p k h
  omega


end GVQCC.ProjectivePivot316
#print axioms GVQCC.ProjectivePivot316.unpivot_pivot
#print axioms GVQCC.ProjectivePivot316.pivot_unpivot
#print axioms GVQCC.ProjectivePivot316.sentinel
#print axioms GVQCC.ProjectivePivot316.old_ratio_collision
#print axioms GVQCC.ProjectivePivot316.regular_recover
#print axioms GVQCC.ProjectivePivot316.singular_recover
#print axioms GVQCC.ProjectivePivot316.repeated_denominator
#print axioms GVQCC.ProjectivePivot316.not_both_zero
#print axioms GVQCC.ProjectivePivot316.bezout_regular
#print axioms GVQCC.ProjectivePivot316.bezout_singular
#print axioms GVQCC.ProjectivePivot316.length_potential
#print axioms GVQCC.ProjectivePivot316.degree_schedule_length
#print axioms GVQCC.ProjectivePivot316.potential_budget
#print axioms GVQCC.ProjectivePivot316.thirtyfive_bound
