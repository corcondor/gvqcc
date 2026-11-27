import Std

namespace GVQCC.V124
def bx (a b : Bool) := Bool.xor a b

-- After a product is copied into a payload, its clean temporary is no
-- longer required coherently. The HMR result can be arbitrary.
theorem product_cleanup (a b m : Bool) :
    bx (m && (a && b)) (m && a && b) = false := by
  cases a <;> cases b <;> cases m <;> decide

-- The guarded scaling word represents 1 + h*(f+1) in characteristic two.
-- Its low coordinate has a constant and a linear term in addition to hf.
def maskLow (h f : Bool) := bx (bx true h) (h && f)
def maskHigh (h f : Bool) := h && f

theorem masked_low_phase (h f m : Bool) :
    bx (m && maskLow h f)
       (bx m (bx (m && h) (m && h && f))) = false := by
  cases h <;> cases f <;> cases m <;> decide
theorem masked_high_phase (h f m : Bool) :
    bx (m && maskHigh h f) (m && h && f) = false := by
  cases h <;> cases f <;> cases m <;> decide
theorem inactive_scale_low (f : Bool) : maskLow false f = true := by
  cases f <;> decide
theorem active_scale_low (f : Bool) : maskLow true f = f := by
  cases f <;> decide

-- A coherent target update may instead be measured and rebuilt from an
-- already-live residual. The phase repayment includes BOTH terms.
theorem residual_rebuild (a b t r m : Bool)
    (h : t = bx (a && b) r) :
    (r, bx (m && t) (bx (m && a && b) (m && r))) =
      (bx t (a && b), false) := by
  rw [h]
  cases a <;> cases b <;> cases r <;> cases m <;> decide

theorem residual_affine (a b c e m : Bool) :
    bx (m && bx (a && b) (bx c e))
       (bx (m && a && b) (bx (m && c) (m && e))) = false := by
  cases a <;> cases b <;> cases c <;> cases e <;> cases m <;> decide

-- Scheduling law. U transforms the source, V uses its transformed value
-- but changes only a disjoint payload; UI restores the source.
def enter {A B : Type} (u : A → A) (s : A × B) := (u s.1,s.2)
def use {A B : Type} (v : A → B → B) (s : A × B) := (s.1,v s.1 s.2)
def leave {A B : Type} (ui : A → A) (s : A × B) := (ui s.1,s.2)

theorem retained_source_two {A B : Type} (u ui : A → A) (v w : A → B → B)
    (h : ∀ a, u (ui a) = a) (s : A × B) :
    leave ui (use w (enter u (leave ui (use v (enter u s))))) =
      leave ui (use w (use v (enter u s))) := by
  rcases s with ⟨a,b⟩
  simp [leave,use,enter,h]

theorem restores_source {A B : Type} (u ui : A → A) (v : A → B → B)
    (h : ∀ a, ui (u a) = a) (s : A × B) :
    (leave ui (use v (enter u s))).1 = s.1 := by
  cases s <;> simp [leave,use,enter,h]

theorem retained_inverse {A B : Type} (inv : A → A) (v w : A → B → B)
    (h : ∀ a, inv (inv a) = a) (s : A × B) :
    leave inv (use w (enter inv (leave inv (use v (enter inv s))))) =
      leave inv (use w (use v (enter inv s))) :=
  retained_source_two inv inv v w h s

#print axioms product_cleanup
#print axioms masked_low_phase
#print axioms masked_high_phase
#print axioms inactive_scale_low
#print axioms active_scale_low
#print axioms residual_rebuild
#print axioms residual_affine
#print axioms retained_source_two
#print axioms restores_source
#print axioms retained_inverse
end GVQCC.V124
