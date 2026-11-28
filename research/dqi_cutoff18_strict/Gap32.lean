import Mathlib
namespace GVQCC.Gap32
variable {R : Type*} [CommRing R]

/-- The two half-degree coordinates of X(X^2+X+r^2)(H^2+s^2 X). -/
theorem padded_split (h2 : (2 : R)=0) (x r s H : R) :
    (x*H+s*x*(x+r))^2+x*((x+r)*H+s*x)^2 =
    x*(x^2+x+r^2)*(H^2+s^2*x) := by
  have sq (a b : R) : (a+b)^2=a^2+b^2 := by
    calc
      _ = a^2+b^2+2*a*b := by ring
      _ = _ := by rw [h2]; ring
  simp only [sq, mul_pow]
  ring

theorem first_remainder (h2 : (2 : R)=0) (x r s H : R) :
    (x*H+s*x*(x+r))+((x+r)*H+s*x) =
    r*H+s*x*(x+r+1) := by
  calc
    _ = r*H+s*x*(x+r+1)+2*x*H := by ring
    _ = _ := by rw [h2]; ring

/-- A degree-one quotient already exposes a cubic remainder.
    This identity does not depend on H or on the chosen root-free quadratic. -/
theorem second_remainder (h2 : (2 : R)=0) (x r s H ri : R)
    (hi : r*ri=1) :
    ((x+r)*H+s*x)+(1+ri*x)*(r*H+s*x*(x+r+1)) =
    ri*s*x*(x^2+x+r^2) := by
  have h : (1+ri*x)*r=x+r := by
    calc
      _ = r+(r*ri)*x := by ring
      _ = _ := by rw [hi]; ring
  have hsq : (x+r)*(x+r+1)+r=x^2+x+r^2 := by
    calc
      _ = x^2+x+r^2+2*(x*r+r) := by ring
      _ = _ := by rw [h2]; ring
  have hri : 1+ri*x=ri*(x+r) := by
    calc
      _ = r*ri+ri*x := by rw [hi]
      _ = _ := by ring
  calc
    _ = ((x+r)*H+(1+ri*x)*r*H) + s*x + (1+ri*x)*(s*x*(x+r+1)) := by ring
    _ = 2*((x+r)*H)+s*x+(1+ri*x)*(s*x*(x+r+1)) := by rw [h]; ring
    _ = s*x+(1+ri*x)*(s*x*(x+r+1)) := by rw [h2]; ring
    _ = ri*s*x*(r+(x+r)*(x+r+1)) := by rw [hri]; calc
      _ = (r*ri)*s*x+ri*(x+r)*(s*x*(x+r+1)) := by rw [hi, one_mul]
      _ = _ := by ring
    _ = ri*s*x*((x+r)*(x+r+1)+r) := by ring
    _ = _ := by rw [hsq]

/-- A nonzero cubic remainder after a degree-16 remainder forces
    the following quotient degree to be 13. The quotient degree
    follows from ordinary Euclidean division's degree law. -/
theorem forced_gap (a b q : Nat) (ha : a=16) (hb : b=3)
    (hdiv : a=b+q) : q=13 := by omega

end GVQCC.Gap32
#print axioms GVQCC.Gap32.padded_split
#print axioms GVQCC.Gap32.first_remainder
#print axioms GVQCC.Gap32.second_remainder
#print axioms GVQCC.Gap32.forced_gap
