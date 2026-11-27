import Std
namespace GVQCC.JetInvolution

variable {A : Type} [DecidableEq A]

def safe (z o : A) (inv : A → A) (x : A) : A :=
  if x = z then o else inv x

theorem safe_cancel (z o : A) (m : A → A → A) (inv : A → A)
    (hh : inv z = z) (hi : ∀ x, inv (inv x) = x)
    (hn : ∀ x, x ≠ z → inv x ≠ z)
    (ho : m o o = o) (hm : ∀ x, x ≠ z → m (inv x) x = o)
    (x : A) : m (safe z o inv x) (safe z o inv (inv x)) = o := by
  by_cases hx : x = z
  · subst x
    simp [safe, hh, ho]
  · have hn' := hn x hx
    simp [safe, hx, hn', hi, hm x hx]

theorem square_cancel (o : A) (m : A → A → A)
    (assoc : ∀ a b c, m (m a b) c = m a (m b c))
    (left : ∀ a, m o a = a) (right : ∀ a, m a o = a)
    (a b v : A) (hab : m a b = o) :
    m (m v (m a a)) (m b b) = v := by
  calc
    _ = m v (m (m a a) (m b b)) := assoc v (m a a) (m b b)
    _ = m v (m a (m a (m b b))) := by rw [assoc a a (m b b)]
    _ = m v (m a (m (m a b) b)) := by rw [assoc a b b]
    _ = m v (m a (m o b)) := by rw [hab]
    _ = m v (m a b) := by rw [left]
    _ = m v o := by rw [hab]
    _ = v := right v

def jet (z o : A) (m : A → A → A) (inv : A → A) (p : A × A) : A × A :=
  (inv p.1, m p.2 (m (safe z o inv p.1) (safe z o inv p.1)))

/-- J² is the identity under the field inverse and multiplication laws, including the zero chart. -/
theorem jet_involution (z o : A) (m : A → A → A) (inv : A → A)
    (hh : inv z = z) (hi : ∀ x, inv (inv x) = x)
    (hn : ∀ x, x ≠ z → inv x ≠ z)
    (assoc : ∀ a b c, m (m a b) c = m a (m b c))
    (left : ∀ a, m o a = a) (right : ∀ a, m a o = a)
    (hm : ∀ x, x ≠ z → m (inv x) x = o)
    (u v : A) : jet z o m inv (jet z o m inv (u,v)) = (u,v) := by
  change (inv (inv u), m (m v (m (safe z o inv u) (safe z o inv u)))
    (m (safe z o inv (inv u)) (safe z o inv (inv u)))) = (u,v)
  rw [hi, square_cancel o m assoc left right _ _ v
    (safe_cancel z o m inv hh hi hn (left o) hm u)]

def bx (a b : Bool) := Bool.xor a b
/-- All five measurement contributions cancel independently of their values. -/
theorem debt_cancel (u v i j f : Bool) :
    bx (bx u (bx v (bx i (bx j f)))) (bx u (bx v (bx i (bx j f)))) = false := by
  cases u <;> cases v <;> cases i <;> cases j <;> cases f <;> decide

#print axioms safe_cancel
#print axioms square_cancel
#print axioms jet_involution
#print axioms debt_cancel
end GVQCC.JetInvolution
