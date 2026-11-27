import Mathlib
namespace GVQCC.V120
variable {F : Type*} [Field F]

theorem scaled_inv_inv (c x : F) (hc : c ≠ 0) :
    c / (c / x) = x := by
  by_cases hx : x = 0
  · simp [hx]
  · field_simp [hc, hx]

/-- The zero chart swaps the roles of the two words. On the finite chart
the first word and its derivative are scaled reciprocal coordinates. -/
noncomputable def jet (c : F) (p : F × F) : F × F := by
  classical
  exact if p.1 = 0 then (0, c / p.2) else (c / p.1, c * p.2 / p.1 ^ 2)

theorem jet_involution (c : F) (hc : c ≠ 0) (p : F × F) :
    jet c (jet c p) = p := by
  classical
  rcases p with ⟨x,y⟩
  by_cases hx : x = 0
  · subst x
    simp [jet, scaled_inv_inv c y hc]
  · have hu : c / x ≠ 0 := div_ne_zero hc hx
    have hv : c * (c * y / x ^ 2) / (c / x) ^ 2 = y := by
      field_simp [hc,hx]
    simp [jet, hx, hu, scaled_inv_inv c x hc, hv]

theorem jet_zero_chart (c : F) (hc : c ≠ 0) (p : F × F) :
    (jet c p).1 = 0 ↔ p.1 = 0 := by
  classical
  by_cases h : p.1 = 0
  · simp [jet,h]
  · simp [jet,h,div_ne_zero hc h]

theorem jet_double_zero (c : F) : jet c (0,0) = (0,0) := by
  classical
  simp [jet]

theorem jet_simple_pole (c y : F) : jet c (0,y) = (0,c/y) := by
  classical
  simp [jet]

/-- On consecutive visits to the same node the first regular transform leaves
a unit numerator. A totalized second quotient equal to zero then uniquely
identifies the singular denominator (not a zero numerator). -/
theorem repeated_pole_detector (n d : F) (hn : n ≠ 0) :
    n/d = 0 ↔ d = 0 := by
  constructor
  · intro h
    by_contra hd
    exact (div_ne_zero hn hd) h
  · intro h
    simp [h]

/-- The pole branch can switch to another quadratic with the same linear term.
The old denominator is a unit modulo the new node. -/
theorem alternate_node_unit (k k' : F) (h : k ≠ k') :
    k-k' ≠ 0 := sub_ne_zero.mpr h

theorem cubic_chart_reconstruct (a b x n0 n1 k : F) :
    a*x^3+(a+b)*x^2+n1*x+n0 =
      (a*x+b)*(x^2+x+k)+(n1-a*k-b)*x+(n0-b*k) := by ring

section Transport
variable {R : Type*} [CommRing R]
def lift (h g : R) (p : R × R) : R × R := (h*p.1+g*p.2,p.1)
theorem lift_scale (h g c : R) (n d : R) :
    lift h g (c*n,c*d) = (c*(lift h g (n,d)).1,c*(lift h g (n,d)).2) := by
  simp [lift]
  ring
theorem lift_injective [IsDomain R] (h g : R) (hg : g ≠ 0) :
    Function.Injective (lift h g) := by
  rintro ⟨n,d⟩ ⟨n',d'⟩ he
  have hn : n = n' := congrArg Prod.snd he
  subst n'
  have hd : h*n+g*d = h*n+g*d' := congrArg Prod.fst he
  have he' : d = d' := mul_left_cancel₀ hg (add_left_cancel hd)
  subst d'
  rfl
end Transport
end GVQCC.V120
#print axioms GVQCC.V120.scaled_inv_inv
#print axioms GVQCC.V120.jet_involution
#print axioms GVQCC.V120.jet_zero_chart
#print axioms GVQCC.V120.jet_double_zero
#print axioms GVQCC.V120.jet_simple_pole
#print axioms GVQCC.V120.repeated_pole_detector
#print axioms GVQCC.V120.alternate_node_unit
#print axioms GVQCC.V120.cubic_chart_reconstruct
#print axioms GVQCC.V120.lift_scale
#print axioms GVQCC.V120.lift_injective
