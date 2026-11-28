import Std
namespace MeasuredAdjoint

def dot : List (Bool × Bool) → Bool
  | [] => false
  | (m,x)::xs => Bool.xor (m && x) (dot xs)

def prior : List (Bool × Bool × Bool) → List (Bool × Bool)
  | [] => []
  | (m,x,_)::xs => (m,x)::prior xs

def direction : List (Bool × Bool × Bool) → List (Bool × Bool)
  | [] => []
  | (m,_,d)::xs => (m,d)::direction xs

def updated (p : Bool) : List (Bool × Bool × Bool) → List (Bool × Bool)
  | [] => []
  | (m,x,d)::xs => (m,Bool.xor x (d && p))::updated p xs

theorem debt_step (m x d p u v : Bool) :
    Bool.xor (m && Bool.xor x (d && p)) (Bool.xor u (v && p)) =
    Bool.xor (Bool.xor (m && x) u) (Bool.xor (m && d) v && p) := by
  cases m <;> cases x <;> cases d <;> cases p <;> cases u <;> cases v <;> rfl

theorem measured_adjoint (p : Bool) (xs : List (Bool × Bool × Bool)) :
    dot (updated p xs) =
    Bool.xor (dot (prior xs)) (dot (direction xs) && p) := by
  induction xs with
  | nil => cases p <;> rfl
  | cons a xs ih =>
    rcases a with ⟨m,x,d⟩
    simp only [dot, updated, prior, direction]
    rw [ih]
    exact debt_step m x d p (dot (prior xs)) (dot (direction xs))

theorem unchanged_control (u a b : Bool) :
    Bool.xor u (false && (a && b)) = u := by cases u <;> rfl

theorem recovered_cx (a b c d : Bool) :
    Bool.xor (c && a) (d && Bool.xor b a) =
    Bool.xor (Bool.xor c d && a) (d && b) := by
  cases a <;> cases b <;> cases c <;> cases d <;> rfl

theorem phase_merge (m a b c : Bool) :
    Bool.xor (m && a) (m && Bool.xor b c) =
    (m && Bool.xor (Bool.xor a b) c) := by
  cases m <;> cases a <;> cases b <;> cases c <;> rfl

theorem measured_old_word (r x p : Bool) :
    Bool.xor (r && Bool.xor x p) (r && p) = (r && x) := by
  cases r <;> cases x <;> cases p <;> rfl

#print axioms debt_step
#print axioms measured_adjoint
#print axioms unchanged_control
#print axioms recovered_cx
#print axioms phase_merge
#print axioms measured_old_word
end MeasuredAdjoint
