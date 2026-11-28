import Mathlib
namespace GVQCC.JointHistoryFree
section Ring
variable {R : Type*} [CommRing R]

theorem gauge_det (a b c d r : R) (h2 : (2:R)=0) :
    a*(d+r*c)+(b+r*a)*c=a*d+b*c := by
  calc
    _ = a*d+b*c+2*(r*a*c) := by ring
    _ = _ := by rw [h2,zero_mul,add_zero]

theorem normalized_bracket (a b c d u : R) :
    a*u*(d*u)+b*u*(c*u)=(a*d+b*c)*u^2 := by ring

theorem scalar_rhs_zero (f v u : R) (hu : u*v=1) (h2 : (2:R)=0) :
    f+f*u*v=0 := by
  calc
    _ = f+f*(u*v) := by ring
    _ = 2*f := by rw [hu]; ring
    _ = _ := by rw [h2,zero_mul]

theorem mixed_rhs_zero (f g v s u : R) (hu : u*v=1) (h2 : (2:R)=0) :
    f+f*u*v=0 ∧ g+f*u*(s*v)+(g+s*f)*u*v=0 := by
  refine ⟨scalar_rhs_zero f v u hu h2,?_⟩
  calc
    _ = g+f*s*(u*v)+(g+s*f)*(u*v) := by ring
    _ = 2*(g+s*f) := by rw [hu]; ring
    _ = _ := by rw [h2,zero_mul]

theorem mixed_inverse (b c x y u : R) (hu : b*u=1) (h2 : (2:R)=0) :
    b*(u*x)=x ∧ b*(u*y+c*u*u*x)+c*(u*x)=y := by
  constructor
  · calc
      _ = (b*u)*x := by ring
      _ = _ := by rw [hu,one_mul]
  · calc
      _ = (b*u)*y+c*u*x*(b*u)+c*u*x := by ring
      _ = y+2*(c*u*x) := by rw [hu]; ring
      _ = _ := by rw [h2,zero_mul,add_zero]

theorem mixed_schur_numerator (x y a c v w d e : R) (h2 : (2:R)=0) :
    (a+(d+e*x)*v)*(y^2*w)+(c+(d+e*y)*w)*(x^2*v)=
      a*(y^2*w)+c*(x^2*v)+(x+y)*v*w*(d*(x+y)+e*x*y) := by
  have hs : (x+y)^2=x^2+y^2 := by
    calc
      _ = x^2+y^2+2*(x*y) := by ring
      _ = _ := by rw [h2,zero_mul,add_zero]
  calc
    _ = a*(y^2*w)+c*(x^2*v)+v*w*(d*(x^2+y^2)+e*x*y*(x+y)) := by ring
    _ = _ := by rw [← hs]; ring

theorem mixed_transpose (x y z s a b : R) :
    (x+a*z+s*(y+b*z),y+b*z)=
      (x+s*y+(a+s*b)*z,y+b*z) := by
  congr 1
  ring

theorem inverse_scale_repay (a u v : R) (h : u*v=1) : (a*u)*v=a := by
  rw [mul_assoc,h,mul_one]

theorem normalized_scalar (a w u p : R) (h : u*u*p=1) :
    (a*u)*(w*u)*p=a*w := by
  calc
    _ = a*w*(u*u*p) := by ring
    _ = _ := by rw [h,mul_one]
end Ring

section Field
variable {F : Type*} [Field F]
theorem pair_marker (b1 b2 : F) (h1 : b1=0) (h2 : b2≠0) :
    (b1=0) ∧ b2≠0 := ⟨h1,h2⟩
theorem scalar_marker (b1 : F) (h : b1≠0) : ¬ b1=0 := h
theorem gauge_collinear (a b c d : F) (ha : a≠0)
    (hp : a*d+b*c=0) : d+(b/a)*c=0 := by
  apply (mul_left_cancel₀ ha)
  calc
    a*(d+(b/a)*c) = a*d+b*c := by field_simp [ha] <;> ring
    _ = a*0 := by rw [hp,mul_zero]
end Field

theorem masked_hmr (g w m : Bool) :
    Bool.xor (m && (g && w)) (m && g && w)=false := by
  cases g <;> cases w <;> cases m <;> decide

theorem gate_debt (old new inverseProduct m : Bool)
    (h : old=inverseProduct) :
    Bool.xor (Bool.xor new (m && old)) (m && inverseProduct)=new := by
  subst old
  cases new <;> cases inverseProduct <;> cases m <;> decide

#print axioms gauge_det
#print axioms normalized_bracket
#print axioms scalar_rhs_zero
#print axioms mixed_rhs_zero
#print axioms mixed_inverse
#print axioms mixed_schur_numerator
#print axioms mixed_transpose
#print axioms inverse_scale_repay
#print axioms normalized_scalar
#print axioms pair_marker
#print axioms scalar_marker
#print axioms gauge_collinear
#print axioms masked_hmr
#print axioms gate_debt
end GVQCC.JointHistoryFree
