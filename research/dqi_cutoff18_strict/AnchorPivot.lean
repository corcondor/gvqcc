import Mathlib
namespace GVQCC.AnchorPivot
open scoped BigOperators

section Field
variable {F : Type*} [Field F]

/-- In a matrix with trivial left kernel, every row contains a nonzero entry.
This is the algebraic precondition on the nonsingular Bezoutian, not a circuit proof. -/
theorem row_nonzero {I : Type*} [Fintype I]
    (B : I → I → F) (i : I)
    (h : ∀ v : I → F, (∀ j, (∑ k, v k * B k j) = 0) → ∀ k, v k = 0) :
    ∃ j, B i j ≠ 0 := by
  classical
  by_contra hn
  push Not at hn
  let v : I → F := fun k => if k = i then 1 else 0
  have hv : ∀ j, (∑ k, v k * B k j) = 0 := by
    intro j
    apply Finset.sum_eq_zero
    intro k _
    by_cases e : k = i
    · subst k
      simp [v, hn]
    · simp [v, e]
  have hz := h v hv i
  simp [v] at hz

theorem nonzero_partner {I : Type*} (B : I → I → F) (i : I)
    (hr : ∃ j, B i j ≠ 0) (hd : B i i = 0) :
    ∃ j, j ≠ i ∧ B i j ≠ 0 := by
  obtain ⟨j, hj⟩ := hr
  refine ⟨j, ?_, hj⟩
  intro e
  subst j
  exact hj hd

/-- A zero diagonal can be handled by a local 2x2 block, even when
the rest of the matrix is not alternating. -/
theorem mixed_block_det (b c : F) (hb : b ≠ 0) :
    0*c-b*b ≠ 0 := by
  rw [zero_mul, zero_sub]
  exact neg_ne_zero.mpr (mul_ne_zero hb hb)

/-- If the chosen partner has nonzero diagonal, two ordinary scalar pivots
suffice. The second pivot is provably nonzero. -/
theorem partner_after_scalar (b c : F) (hb : b ≠ 0) (hc : c ≠ 0) :
    (0:F)-b*b/c ≠ 0 := by
  rw [zero_sub]
  exact neg_ne_zero.mpr (div_ne_zero (mul_ne_zero hb hb) hc)

/-- Direct inverse action of the mixed 2x2 block. -/
theorem mixed_block_solve (b c x y : F) (hb : b ≠ 0) :
    b*(x/b) = x ∧ b*((y-c*(x/b))/b)+c*(x/b) = y := by
  have cancel (u : F) : b*(u/b) = u := by
    rw [mul_comm, div_mul_cancel₀ _ hb]
  constructor
  · exact cancel x
  · rw [cancel, sub_add_cancel]

/-- A source pair has a nonzero local orientation under coprimality. -/
theorem local_orientation (a b : F) (h : a ≠ 0 ∨ b ≠ 0) [Decidable (b = 0)] :
    (if b = 0 then a else b) ≠ 0 := by
  by_cases hb : b = 0
  · simp only [hb, ite_true]
    exact h.resolve_right (fun hn => hn hb)
  · simp only [hb, ite_false]
    exact hb

end Field

section Ring
variable {R : Type*} [CommRing R]

/-- A characteristic-two shear has an exact inverse. -/
theorem anchor_shear (a p w : R) (h : (2:R)=0) :
    (a+p*w)+p*w = a := by
  calc
    _ = a+2*(p*w) := by ring
    _ = _ := by rw [h,zero_mul,add_zero]

/-- Pull a phase covector back through a two-coordinate shear. -/
theorem adjoint_shear (a b p m n : R) :
    m*(a+p*b)+n*b = m*a+(n+m*p)*b := by ring

/-- The two opposite repayments cancel, including when the target is dirty. -/
theorem adjoint_repay (x m n : R) (h : (2:R)=0) :
    x+m*n+m*n=x := by
  calc
    _ = x+2*(m*n) := by ring
    _ = _ := by rw [h,zero_mul,add_zero]

end Ring

#print axioms row_nonzero
#print axioms nonzero_partner
#print axioms mixed_block_det
#print axioms partner_after_scalar
#print axioms mixed_block_solve
#print axioms local_orientation
#print axioms anchor_shear
#print axioms adjoint_shear
#print axioms adjoint_repay

section PackedOrientation
variable {F : Type*} [Field F] [DecidableEq F]

/-- The retired pair stores the local orientation without an extra history bit. -/
theorem packed_orientation_restore (f : Bool) (a r : F)
    (ha : a ≠ 0) (hr : f = true → r = 0) :
    let p := if f then (r,a) else (a,r)
    (if p.1 = 0 then (true,p.2,p.1) else (false,p.1,p.2)) = (f,a,r) := by
  cases f
  · simp [ha]
  · have hz := hr rfl
    simp [hz]

omit [DecidableEq F] in
theorem oriented_ratio_zero (a : F) : (0:F)/a = 0 := zero_div a

omit [DecidableEq F] in
theorem retired_scale_nonzero (a h : F) (ha : a ≠ 0) (hh : h ≠ 0) :
    a/h ≠ 0 := div_ne_zero ha hh

end PackedOrientation

#print axioms packed_orientation_restore
#print axioms oriented_ratio_zero
#print axioms retired_scale_nonzero

end GVQCC.AnchorPivot
