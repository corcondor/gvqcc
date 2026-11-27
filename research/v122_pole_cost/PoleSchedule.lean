import Init
namespace GVQCC.PoleSchedule
def bx (a b : Bool) := Bool.xor a b
def dot : List (Bool × Bool) → Bool
  | [] => false
  | (a,b)::xs => bx (a && b) (dot xs)
theorem dot_append (xs ys : List (Bool × Bool)) :
    dot (xs ++ ys) = bx (dot xs) (dot ys) := by
  induction xs with
  | nil => cases dot ys <;> rfl
  | cons p ps ih =>
    rcases p with ⟨a,b⟩
    simp only [List.cons_append,dot,ih]
    cases a <;> cases b <;> cases dot ps <;> cases dot ys <;> rfl
theorem phase_product (m a b : Bool) :
    bx (m && (a && b)) (m && a && b) = false := by
  cases m <;> cases a <;> cases b <;> decide
theorem phase_affine_mask (m h f : Bool) :
    bx (m && bx (bx true h) (h && f))
       (bx m (bx (m && h) (m && h && f))) = false := by
  cases m <;> cases h <;> cases f <;> decide
theorem phase_mask (m h f : Bool) :
    bx (m && (h && f)) (m && h && f) = false := by
  cases m <;> cases h <;> cases f <;> decide
-- Scope transport: U computes f; V acts on disjoint payload using the
-- materialized f; U^{-1} can remain deferred until its last consumer.
theorem disjoint_commute {A B : Type} (u : A → A) (v : B → B) (a : A) (b : B) :
    (u a,v b) = (u a,v b) := rfl
def actA {A B : Type} (u : A → A) (p : A × B) := (u p.1,p.2)
def actB {A B : Type} (v : B → B) (p : A × B) := (p.1,v p.2)
theorem commute {A B : Type} (u : A → A) (v : B → B) (p : A × B) :
    actB v (actA u p) = actA u (actB v p) := by cases p <;> rfl
theorem cancel_chart {A B : Type} (u ui : A → A) (v : B → B)
    (hi : ∀ a, u (ui a) = a) (p : A × B) :
    actA u (actB v (actA ui p)) = actB v p := by
  rcases p with ⟨a,b⟩
  simp [actA,actB,hi]
theorem defer_chart {A B : Type} (u ui : A → A) (v : B → B)
    (hi : ∀ a, u (ui a) = a) (a : A) (b : B) :
    (u (ui a),v b) = (a,v b) := by rw [hi]
end GVQCC.PoleSchedule
#print axioms GVQCC.PoleSchedule.dot_append
#print axioms GVQCC.PoleSchedule.phase_product
#print axioms GVQCC.PoleSchedule.phase_affine_mask
#print axioms GVQCC.PoleSchedule.phase_mask
#print axioms GVQCC.PoleSchedule.commute
#print axioms GVQCC.PoleSchedule.cancel_chart
#print axioms GVQCC.PoleSchedule.defer_chart
