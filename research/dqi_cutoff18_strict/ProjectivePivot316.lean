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

/-- The missing flag cannot be dropped when the denominator is zero.
Both axes produce the same output of the old zero-safe ratio formula. -/
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

/-- In either admissible chart the new denominator remains nonzero
under the SAME residue evaluation. This justifies the zero sentinel
on repeated nodes, not on an arbitrary next distinct node. -/
theorem repeated_denominator (ev : R →+* F) (n d : R)
    (hd : ev d ≠ 0) :
    ev (if ev n = 0 then d else n) ≠ 0 := by
  by_cases hn : ev n = 0
  · simp [hn,hd]
  · simp [hn]

end PolynomialStep

end GVQCC.ProjectivePivot316
#print axioms GVQCC.ProjectivePivot316.unpivot_pivot
#print axioms GVQCC.ProjectivePivot316.pivot_unpivot
#print axioms GVQCC.ProjectivePivot316.sentinel
#print axioms GVQCC.ProjectivePivot316.old_ratio_collision
#print axioms GVQCC.ProjectivePivot316.regular_recover
#print axioms GVQCC.ProjectivePivot316.singular_recover
#print axioms GVQCC.ProjectivePivot316.repeated_denominator
