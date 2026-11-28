import Std
namespace SharedRightGroup

structure Entry where
  rightBit : Bool
  selected : Bool
  matrixBit : Bool

def oldSlice : List Entry → Bool
  | [] => false
  | e :: es => Bool.xor (e.rightBit && e.matrixBit) (oldSlice es)

def supportSlice : List Entry → Bool
  | [] => false
  | e :: es => Bool.xor (e.rightBit && e.selected) (supportSlice es)

def newSlice (p : Bool) : List Entry → Bool
  | [] => false
  | e :: es =>
      Bool.xor (e.rightBit && Bool.xor e.matrixBit (e.selected && p)) (newSlice p es)

theorem step (v s m p a b : Bool) :
    Bool.xor (v && Bool.xor m (s && p)) (Bool.xor a (b && p)) =
      Bool.xor (Bool.xor (v && m) a) (Bool.xor (v && s) b && p) := by
  cases v <;> cases s <;> cases m <;> cases p <;> cases a <;> cases b <;> decide

theorem update_all (p : Bool) (xs : List Entry) :
    newSlice p xs = Bool.xor (oldSlice xs) (supportSlice xs && p) := by
  induction xs with
  | nil => cases p <;> decide
  | cons e es ih =>
    simp only [newSlice, oldSlice, supportSlice, ih]
    exact step e.rightBit e.selected e.matrixBit p (oldSlice es) (supportSlice es)

theorem zero_sum_preserves (p : Bool) (xs : List Entry)
    (h : supportSlice xs = false) : newSlice p xs = oldSlice xs := by
  rw [update_all, h]
  cases p <;> cases oldSlice xs <;> decide

theorem all_slices_preserved (p : Bool) (xs : Nat → List Entry)
    (h : ∀ j, supportSlice (xs j) = false) :
    ∀ j, newSlice p (xs j) = oldSlice (xs j) :=
  fun j => zero_sum_preserves p (xs j) (h j)

theorem count_pairs : (255 : Nat) * 255 * (2^11 - 1) = 133106175 := by decide
theorem full_static_target : (317994 : Nat) - 333 * (99 - 97) = 317328 := by decide
#print axioms step
#print axioms update_all
#print axioms zero_sum_preserves
#print axioms all_slices_preserved
#print axioms count_pairs
#print axioms full_static_target
end SharedRightGroup
