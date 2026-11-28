import Mathlib

namespace GVQCC.FrameSplice283
open scoped BigOperators

section Frame
variable {F : Type*} [Field F]
variable {V W U : Type*}
variable [AddCommGroup V] [Module F V]
variable [AddCommGroup W] [Module F W]
variable [AddCommGroup U] [Module F U]

/-- A rank-one update in a mutable target coordinate frame acts on any
    incoming target, including a dirty target. -/
theorem rank_update_conjugate (T : V ≃ₗ[F] W)
    (z v : V) (a b : F) :
    T.symm (T z+(a*b) • T v)=z+(a*b) • v := by
  simp

/-- The correct contragredient evaluation of an input linear form. -/
theorem source_form_transport (A : V ≃ₗ[F] W)
    (ell : V →ₗ[F] F) (x : V) :
    (ell.comp A.symm.toLinearMap) (A x)=ell x := by
  simp

/-- Change between two live affine bases without changing the represented
    source. No fresh storage or reset is required in this semantics. -/
theorem frame_transition (A : V ≃ₗ[F] W) (B : V ≃ₗ[F] U) (x : V) :
    (B.toLinearMap.comp A.symm.toLinearMap) (A x)=B x := by
  simp

theorem frame_transition_inverse (A : V ≃ₗ[F] W) (B : V ≃ₗ[F] U) (w : W) :
    A (B.symm (B (A.symm w)))=w := by simp

/-- One actual transposed term, with both input forms transported and
    the target direction in its current basis. -/
theorem rank_term_transport (A : V ≃ₗ[F] V) (P : W ≃ₗ[F] W)
    (T : U ≃ₗ[F] U) (a : V →ₗ[F] F) (b : W →ₗ[F] F)
    (v z : U) (x : V) (y : W) :
    T.symm (T z+
      ((a.comp A.symm.toLinearMap) (A x) *
       (b.comp P.symm.toLinearMap) (P y)) • T v) =
        z+(a x*b y) • v := by simp

/-- Two RHS transformations sharing the same left coefficient evaluation. -/
theorem two_rhs_transport (A : V ≃ₗ[F] V) (P : W ≃ₗ[F] W)
    (T : U ≃ₗ[F] U) (a : V →ₗ[F] F) (b : W →ₗ[F] F)
    (v z₀ z₁ : U) (x : V) (y₀ y₁ : W) :
    (T.symm (T z₀+((a.comp A.symm.toLinearMap) (A x)*
      (b.comp P.symm.toLinearMap) (P y₀)) • T v),
     T.symm (T z₁+((a.comp A.symm.toLinearMap) (A x)*
      (b.comp P.symm.toLinearMap) (P y₁)) • T v)) =
     (z₀+(a x*b y₀) • v,z₁+(a x*b y₁) • v) := by simp

end Frame

section Fold
variable {A : Type*} [AddCommGroup A]

/-- Arbitrarily many rank-one directions may be accumulated in-place. -/
theorem fold_add_eq (xs : List A) (z : A) :
    xs.foldl (fun a b => a+b) z = z+xs.sum := by
  induction xs generalizing z with
  | nil => simp
  | cons x xs ih =>
      simp only [List.foldl_cons,List.sum_cons,ih,add_assoc]

theorem reorder_independent_terms (xs ys : List A) (z : A)
    (h : xs.Perm ys) :
    xs.foldl (fun a b => a+b) z=ys.foldl (fun a b => a+b) z := by
  rw [fold_add_eq,fold_add_eq,h.sum_eq]

theorem fold_sub_undo (xs : List A) (z : A) :
    xs.foldl (fun a b => a-b) (z+xs.sum)=z := by
  induction xs generalizing z with
  | nil => simp
  | cons x xs ih =>
      simp only [List.foldl_cons,List.sum_cons]
      have h : z+(x+xs.sum)-x=z+xs.sum := by abel
      rw [h,ih]

end Fold

section Phase
variable {I J : Type*} [Fintype I] [Fintype J]

/-- Binary linear mask transfer, including a nonzero affine offset.
    The final summand is the global phase from the offset. -/
theorem affine_phase_pullback (M : I → J → ZMod 2) (c m : I → ZMod 2)
    (x : J → ZMod 2) :
    (∑ i,m i*((∑ j,M i j*x j)+c i)) =
      (∑ j,(∑ i,m i*M i j)*x j)+(∑ i,m i*c i) := by
  simp only [mul_add,Finset.sum_add_distrib,Finset.mul_sum,Finset.sum_mul]
  congr 1
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro i _
  ring

/-- If the correction is linear, residual additivity is necessary.
    A counterexample on fixed support rules out that correction class. -/
theorem nonadditive_not_linear {A : Type*} [AddCommGroup A]
    (f : A → A) (x y : A)
    (h : f (x+y) ≠ f x+f y) :
    ¬ ∃ L : A →+ A, ∀ a,L a=f a := by
  rintro ⟨L,hL⟩
  apply h
  rw [← hL (x+y),map_add,hL x,hL y]

omit [Fintype I] in
/-- A fixed-support syndrome map is linear in the amplitudes. -/
theorem syndrome_amplitude_add {F : Type*} [Field F]
    (M : I → J → F) (u v : J → F) (i : I) :
    (∑ j,M i j*(u j+v j)) =
      (∑ j,M i j*u j)+(∑ j,M i j*v j) := by
  simp only [mul_add,Finset.sum_add_distrib]

/-- A nonadditive residual on a fixed linear chart excludes every
    additive correction of the syndrome, even after a linear embedding. -/
theorem chart_nonadditivity {A B C : Type*}
    [AddCommGroup A] [AddCommGroup B] [AddCommGroup C]
    (S : A →+ B) (err : A → C) (u v : A)
    (h : err (u+v) ≠ err u+err v) :
    ¬ ∃ L : B →+ C, ∀ a,L (S a)=err a := by
  rintro ⟨L,hL⟩
  apply h
  rw [← hL (u+v),map_add,map_add,hL u,hL v]

end Phase

section Tape
variable {S : Type*}

def execute (gates : List (S → S)) (s : S) : S :=
  gates.foldl (fun x g => g x) s

theorem execute_append (p q : List (S → S)) (s : S) :
    execute (p++q) s=execute q (execute p s) := by
  simp [execute,List.foldl_append]

/-- Exact local replacement is compositional for arbitrary prefix and
    suffix. This is the semantic obligation of the #283 interval splice. -/
theorem splice_preserves (p old new q : List (S → S))
    (he : ∀ s, execute old s=execute new s) (s : S) :
    execute (p++old++q) s=execute (p++new++q) s := by
  simp only [execute_append,he]

/-- A weaker, explicitly stated precondition is also sufficient if
    the unchanged prefix establishes it. -/
theorem splice_on_invariant (p old new q : List (S → S))
    (Inv : S → Prop) (hp : ∀ s,Inv (execute p s))
    (he : ∀ s,Inv s → execute old s=execute new s) (s : S) :
    execute (p++old++q) s=execute (p++new++q) s := by
  simp only [execute_append,he _ (hp s)]

end Tape

#print axioms rank_update_conjugate
#print axioms source_form_transport
#print axioms frame_transition
#print axioms frame_transition_inverse
#print axioms rank_term_transport
#print axioms two_rhs_transport
#print axioms fold_add_eq
#print axioms reorder_independent_terms
#print axioms fold_sub_undo
#print axioms affine_phase_pullback
#print axioms nonadditive_not_linear
#print axioms syndrome_amplitude_add
#print axioms chart_nonadditivity
#print axioms execute_append
#print axioms splice_preserves
#print axioms splice_on_invariant
end GVQCC.FrameSplice283
