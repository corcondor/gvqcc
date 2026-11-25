import Std.Tactic
namespace GVQCC.V66

-- A product's output is transported in a persistent linear frame.
theorem transported_update {V : Type} (add : V → V → V) (A : V → V)
    (hA : ∀ x d, A (add x d) = add (A x) (A d)) (x d : V) :
    add (A x) (A d) = A (add x d) := (hA x d).symm

-- Changing an output coordinate before/after its neighbour's update.
theorem fanout_transport (a b f : Bool) :
    (Bool.xor a f, Bool.xor (Bool.xor a b) (Bool.xor a f)) =
    (Bool.xor a f, Bool.xor b f) := by
  cases a <;> cases b <;> cases f <;> decide

-- Two factors differing by the common control; linear residual included.
theorem shared_factor (u v w : Bool) :
    Bool.xor (u && v) (u && w) = (u && Bool.xor v w) := by
  cases u <;> cases v <;> cases w <;> decide

theorem polar_exchange (u v : Bool) :
    (u && Bool.xor u v) = Bool.xor (u && v) u := by
  cases u <;> cases v <;> decide

theorem measured_product (m u v : Bool) :
    Bool.xor (m && (u && v)) (m && u && v) = false := by
  cases m <;> cases u <;> cases v <;> decide

-- Discrete integration by parts over GF(2).
theorem abel_two (a b c k l : Bool) :
    Bool.xor (k && Bool.xor a b) (l && Bool.xor b c) =
      Bool.xor (Bool.xor (k && a) (Bool.xor k l && b)) (l && c) := by
  cases a <;> cases b <;> cases c <;> cases k <;> cases l <;> decide

def xorList : List Bool → Bool
  | [] => false
  | a :: xs => Bool.xor a (xorList xs)
def edges (a : Bool) : List Bool → List Bool
  | [] => []
  | b :: bs => Bool.xor a b :: edges b bs
def endpoint (a : Bool) : List Bool → Bool
  | [] => a
  | b :: bs => endpoint b bs

theorem telescope (a : Bool) (bs : List Bool) :
    xorList (edges a bs) = Bool.xor a (endpoint a bs) := by
  induction bs generalizing a with
  | nil => cases a <;> rfl
  | cons b bs ih =>
    change Bool.xor (Bool.xor a b) (xorList (edges b bs)) =
      Bool.xor a (endpoint b bs)
    rw [ih]
    cases h : endpoint b bs <;> cases a <;> cases b <;> rfl

theorem resource_receipt :
    305655 - 171605 = 134050 ∧
    561982 - 390675 = 171307 ∧
    30 * 1219 = 36570 ∧ 2 * 1543 = 3086 ∧
    5 * 1219 = 6095 ∧ 6095 - 5617 = 478 := by decide

end GVQCC.V66
