import Std

namespace BoundaryPhase

def dot : List (Bool × Bool) → Bool
  | [] => false
  | (k,s)::xs => Bool.xor (k && s) (dot xs)

def pre : List (Bool × Bool × Bool) → List (Bool × Bool)
  | [] => []
  | (k,s,_)::xs => (k,s)::pre xs

def post : List (Bool × Bool × Bool) → List (Bool × Bool)
  | [] => []
  | (k,s,d)::xs => (k,Bool.xor s d)::post xs

def delta : List (Bool × Bool × Bool) → List (Bool × Bool)
  | [] => []
  | (k,_,d)::xs => (k,d)::delta xs

private theorem scalar (k s d x y z : Bool)
    (h : Bool.xor x y = z) :
    Bool.xor (Bool.xor (k && s) x)
      (Bool.xor (k && Bool.xor s d) y) = Bool.xor (k && d) z := by
  cases k <;> cases s <;> cases d <;> cases x <;> cases y <;> cases z <;> simp_all

theorem pay_between (xs : List (Bool × Bool × Bool)) :
    Bool.xor (dot (pre xs)) (dot (post xs)) = dot (delta xs) := by
  induction xs with
  | nil => rfl
  | cons v xs ih =>
    rcases v with ⟨k,s,d⟩
    simp only [dot, pre, post, delta]
    exact scalar k s d (dot (pre xs)) (dot (post xs)) (dot (delta xs)) ih

#print axioms pay_between
end BoundaryPhase
