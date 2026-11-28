import Mathlib
namespace GVQCC.FixedAnchorCovariance
open scoped BigOperators

section Field
variable {F : Type*} [Field F]

/-- The local derivative pivot equals the original oriented source times
the retired first divided-difference value in characteristic two. -/
theorem confluent_pivot (a b ap bp : F) (ha : a ≠ 0) :
    a * (bp+(b/a)*ap)=a*bp+b*ap := by
  field_simp [ha]
  ring

theorem confluent_unit (a b ap bp : F) (ha : a ≠ 0)
    (hd : a*bp+b*ap ≠ 0) : bp+(b/a)*ap ≠ 0 := by
  intro h
  apply hd
  rw [← confluent_pivot a b ap bp ha,h,mul_zero]

/-- Nonzero evaluation makes the triangular interpolation coordinate
exchange reversible. -/
theorem rebase_inverse (u x v : F) (hu : u ≠ 0) :
    (u*x+v-v)/u=x := by
  rw [add_sub_cancel_right]
  field_simp [hu]

theorem rebase_adjoint (u x y s m n : F) :
    m*(u*x+s*y)+n*y=(m*u)*x+(n+m*s)*y := by ring

/-- A root-free padding factor cancels from the physical residue.
The argument is conditional on the actual locator derivative. -/
theorem padding_cancel (g a b : F) (hg : g ≠ 0) (ha : a ≠ 0) :
    g*b/(g*a)=b/a := by
  field_simp [hg,ha]

theorem padding_exchange (g h a b : F) (hg : g ≠ 0)
    (hh : h ≠ 0) (ha : a ≠ 0) : g*b/(g*a)=h*b/(h*a) := by
  rw [padding_cancel g a b hg ha,padding_cancel h a b hh ha]

/-- No modular inverse is asserted when a padding factor divides D. -/
theorem nonunit_no_inverse (x : F) (hx : x = 0) : ¬ ∃ y, x*y=1 := by
  rw [hx]
  simp

/-- Exact covariance of every syndrome moment under a fixed nonzero
multiplicative coordinate change. No sampling or weight assumption. -/
theorem moment_scale {I : Type*} [Fintype I] (e x : I → F)
    (c : F) (n : ℕ) :
    (∑ j, e j*(c*x j)^n)=c^n*(∑ j,e j*x j^n) := by
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro j _
  rw [mul_pow]
  ring

theorem scale_inverse (c x : F) (hc : c ≠ 0) :
    (c*x)/c=x := by
  field_simp [hc]

end Field

section Phase
variable {I : Type*} [Fintype I]
/-- Abstract arbitrary phase pairing: a permutation of both arguments
preserves the finite sum. -/
theorem phase_permutation (σ : I ≃ I) (p : I → ZMod 2) :
    (∑ j, p (σ j)) = ∑ j, p j := by
  exact Equiv.sum_comp σ p
end Phase

theorem native_frame_budget : 67549292+2*4361=67558014 := by decide

#print axioms confluent_pivot
#print axioms confluent_unit
#print axioms rebase_inverse
#print axioms rebase_adjoint
#print axioms padding_cancel
#print axioms padding_exchange
#print axioms nonunit_no_inverse
#print axioms moment_scale
#print axioms scale_inverse
#print axioms phase_permutation
#print axioms native_frame_budget
end GVQCC.FixedAnchorCovariance
