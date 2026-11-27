import Mathlib
namespace GVQCC.WeightedHalfFFT
variable {F : Type*} [Field F]

/-- A weighted residue need not be unweighted on quantum wires:
the inverse weight may instead be transported into the phase functional. -/
theorem weighted_root_residue (x u d p v : F)
    (hx : x ≠ 0) (hu : u ≠ 0) (hd : d ≠ 0)
    (hv : v*d = u*p) :
    v/(x*u) = p/(x*d) := by
  apply (div_eq_div_iff (mul_ne_zero hx hu) (mul_ne_zero hx hd)).2
  calc
    v*(x*d) = x*(v*d) := by ring
    _ = x*(u*p) := by rw [hv]
    _ = p*(x*u) := by ring

theorem weighted_half_identity (h2 : (2 : F) = 0)
    (x a b p0 p1 s t z w u d e : F)
    (hz : b*z = p0+a*s) (hw : b*w = p1+a*t)
    (hr : a^2+x*b^2=0) (hd : d=b^2)
    (hp : p0^2+x*p1^2=(u*x*e)*d)
    (hb : b ≠ 0) :
    (z+x*t)^2+x*(w+s)^2 = u*x*e := by
  have hsq (r v : F) : (r+v)^2 = r^2+v^2 := by
    calc
      _ = r^2+v^2+2*r*v := by ring
      _ = r^2+v^2 := by rw [h2]; ring
  have h1 : b*(z+x*t)=p0+a*s+x*b*t := by
    calc
      _ = b*z+x*b*t := by ring
      _ = _ := by rw [hz]
  have h2' : b*(w+s)=p1+a*t+b*s := by
    calc
      _ = b*w+b*s := by ring
      _ = _ := by rw [hw]
  apply mul_left_cancel₀ (pow_ne_zero 2 hb)
  calc
    b^2*((z+x*t)^2+x*(w+s)^2) =
        (b*(z+x*t))^2+x*(b*(w+s))^2 := by ring
    _ = (p0+a*s+x*b*t)^2+x*(p1+a*t+b*s)^2 := by rw [h1,h2']
    _ = p0^2+x*p1^2+(a^2+x*b^2)*(s^2+x*t^2) := by
      simp only [hsq, mul_pow]; ring
    _ = b^2*(u*x*e) := by rw [hr,zero_mul,add_zero,hp,hd]; ring

/-- Three reversible split updates on a shared coefficient restore the bank. -/
theorem fft_split_cycle (h2 : (2 : F)=0) (a b c : F) :
    ((a+c*b)+b)+(c+1)*b=a := by
  calc
    _ = a+2*(c+1)*b := by ring
    _ = a := by rw [h2]; ring

/-- The classical mask adjoint identity on a finite binary vector space. -/
theorem phase_adjoint {I J : Type*} [Fintype I] [Fintype J]
    (A : I → J → ZMod 2) (x : J → ZMod 2) (m : I → ZMod 2) :
    (∑ i, m i * (∑ j, A i j*x j)) =
    ∑ j, (∑ i, A i j*m i)*x j := by
  simp only [Finset.mul_sum,Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro i _
  ring

end GVQCC.WeightedHalfFFT
#print axioms GVQCC.WeightedHalfFFT.weighted_root_residue
#print axioms GVQCC.WeightedHalfFFT.weighted_half_identity
#print axioms GVQCC.WeightedHalfFFT.fft_split_cycle
#print axioms GVQCC.WeightedHalfFFT.phase_adjoint
