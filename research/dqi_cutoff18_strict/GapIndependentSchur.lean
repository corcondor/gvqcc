import Mathlib
namespace GVQCC.GapIndependentSchur
variable {R : Type*} [CommRing R]

/-- The 1-pivot Bezoutian Schur update, with w_x and w_y the divided brackets. -/
theorem one_pivot (x y t ax bx ay byy a b u wx wy : R)
    (h2 : (2 : R) = 0)
    (hx : (x+t)*wx = ax*b+bx*a)
    (hy : (y+t)*wy = ay*b+byy*a) :
    (ax+u*wx*a)*(byy+u*wy*b)+(bx+u*wx*b)*(ay+u*wy*a) =
      ax*byy+bx*ay+u*(x+y)*wx*wy := by
  calc
    _ = ax*byy+bx*ay+u*wy*(ax*b+bx*a)+u*wx*(ay*b+byy*a)+
          2*(u*u*wx*wy*a*b) := by ring
    _ = ax*byy+bx*ay+u*(x+y)*wx*wy+
          2*(u*t*wx*wy+u*u*wx*wy*a*b) := by
      rw [← hx, ← hy]
      ring
    _ = _ := by rw [h2, zero_mul, add_zero]

/-- A nonsingular alternating 2-pivot has inverse [[0,u],[u,0]], u*k=1. -/
theorem alternating_pivot (x y t s ax bx ay byy a b c d u k wx1 wx2 wy1 wy2 : R)
    (h2 : (2 : R) = 0) (hu : u*k = 1)
    (hxp : (x+t)*wx1 = ax*b+bx*a)
    (hxq : (x+s)*wx2 = ax*d+bx*c)
    (hyp : (y+t)*wy1 = ay*b+byy*a)
    (hyq : (y+s)*wy2 = ay*d+byy*c)
    (hpq : (t+s)*k = a*d+b*c) :
    (ax+u*(wx2*a+wx1*c))*(byy+u*(wy2*b+wy1*d))+
    (bx+u*(wx2*b+wx1*d))*(ay+u*(wy2*a+wy1*c)) =
      ax*byy+bx*ay+u*(x+y)*(wx1*wy2+wx2*wy1) := by
  have hu2 : u*u*k = u := by
    calc
      u*u*k = u*(u*k) := by ring
      _ = u := by rw [hu, mul_one]
  calc
    _ = ax*byy+bx*ay+
      u*(wy2*(ax*b+bx*a)+wy1*(ax*d+bx*c)+
         wx2*(ay*b+byy*a)+wx1*(ay*d+byy*c))+
      u*u*(wx1*wy2+wx2*wy1)*(a*d+b*c)+
      2*(u*u*(wx2*wy2*a*b+wx1*wy1*c*d)) := by ring
    _ = ax*byy+bx*ay+u*(x+y+t+s)*(wx1*wy2+wx2*wy1)+
      (u*u*k)*(t+s)*(wx1*wy2+wx2*wy1)+
      2*(u*u*(wx2*wy2*a*b+wx1*wy1*c*d)) := by
      rw [← hxp, ← hxq, ← hyp, ← hyq, ← hpq]
      ring
    _ = ax*byy+bx*ay+u*(x+y)*(wx1*wy2+wx2*wy1)+
      2*(u*(t+s)*(wx1*wy2+wx2*wy1)+
         u*u*(wx2*wy2*a*b+wx1*wy1*c*d)) := by
      rw [hu2]
      ring
    _ = _ := by rw [h2, zero_mul, add_zero]

/-- The original 1-pivot divided bracket is unchanged byy its own transvection. -/
theorem one_bracket (a b p q u w : R) (h2 : (2 : R) = 0) :
    (a+u*w*p)*q+(b+u*w*q)*p = a*q+b*p := by
  calc
    _ = a*q+b*p+2*(u*w*p*q) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

/-- For a 2-pivot, each divided bracket gains precisely the other factor. -/
theorem two_bracket_left (x t s ax bx a b c d u k w1 w2 : R)
    (h2 : (2 : R) = 0) (hu : u*k = 1)
    (hx : (x+t)*w1 = ax*b+bx*a)
    (hpq : (t+s)*k = a*d+b*c) :
    (ax+u*(w2*a+w1*c))*b+(bx+u*(w2*b+w1*d))*a =
      (x+s)*w1 := by
  have hh : u*w1*((t+s)*k) = w1*(t+s) := by
    calc
      _ = (u*k)*(w1*(t+s)) := by ring
      _ = _ := by rw [hu, one_mul]
  calc
    _ = ax*b+bx*a+u*w1*(a*d+b*c)+2*(u*w2*a*b) := by ring
    _ = (x+t)*w1+w1*(t+s) := by
      rw [← hx, ← hpq, hh, h2, zero_mul, add_zero]
    _ = (x+s)*w1+2*(t*w1) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

theorem two_bracket_right (x t s ax bx a b c d u k w1 w2 : R)
    (h2 : (2 : R) = 0) (hu : u*k = 1)
    (hx : (x+s)*w2 = ax*d+bx*c)
    (hpq : (t+s)*k = a*d+b*c) :
    (ax+u*(w2*a+w1*c))*d+(bx+u*(w2*b+w1*d))*c =
      (x+t)*w2 := by
  have hh : u*w2*((t+s)*k) = w2*(t+s) := by
    calc
      _ = (u*k)*(w2*(t+s)) := by ring
      _ = _ := by rw [hu, one_mul]
  calc
    _ = ax*d+bx*c+u*w2*(a*d+b*c)+2*(u*w1*c*d) := by ring
    _ = (x+s)*w2+w2*(t+s) := by
      rw [← hx, ← hpq, hh, h2, zero_mul, add_zero]
    _ = (x+t)*w2+2*(s*w2) := by ring
    _ = _ := by rw [h2, zero_mul, add_zero]

theorem transvection_restore (a b p q u w : R)
    (h2 : (2 : R) = 0) :
    ((a+u*w*p)+u*w*p, (b+u*w*q)+u*w*q) = (a,b) := by
  have ha : (a+u*w*p)+u*w*p = a+2*(u*w*p) := by ring
  have hb : (b+u*w*q)+u*w*q = b+2*(u*w*q) := by ring
  rw [ha,hb,h2,zero_mul,zero_mul,add_zero,add_zero]

theorem source_word_budget (n k : ℕ) (h : k ≤ n) :
    2*(n-k+1)+2*k=2*(n+1) := by omega
theorem packed_polynomial_words : 2*(17+1)+2*17+1=71 := by decide

#print axioms one_pivot
#print axioms alternating_pivot
#print axioms one_bracket
#print axioms two_bracket_left
#print axioms two_bracket_right
#print axioms transvection_restore
#print axioms source_word_budget
#print axioms packed_polynomial_words
end GVQCC.GapIndependentSchur
