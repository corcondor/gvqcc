import Std
namespace V55
def bx (a b : Bool) : Bool := Bool.xor a b
def val (a : Bool) : Int := if a then 1 else 0
def chi (a : Bool) : Int := if a then -1 else 1
theorem coset2 (s d h : Bool) :
    chi s + chi h * chi (bx s d) =
      (if d = h then 2 * chi s else 0) := by
  cases s <;> cases d <;> cases h <;> decide
theorem coset4 (s a b h k : Bool) :
    chi s + chi h * chi (bx s a) + chi k * chi (bx s b) +
    chi h * chi k * chi (bx (bx s a) b) =
      (if a = h ∧ b = k then 4 * chi s else 0) := by
  cases s <;> cases a <;> cases b <;> cases h <;> cases k <;> decide
theorem signed_translation (s f : Bool) :
    val (bx s f) - val s = val f * chi s := by
  cases s <;> cases f <;> decide
theorem product_erase (m a b : Bool) :
    bx (m && (a && b)) (m && (a && b)) = false := by
  cases m <;> cases a <;> cases b <;> decide
theorem prefix_sibling (p q : Bool) :
    bx (p && q) p = (p && !q) := by
  cases p <;> cases q <;> decide
theorem telescoping (m a b c : Bool) :
    bx (m && bx a b) (m && bx b c) = (m && bx a c) := by
  cases m <;> cases a <;> cases b <;> cases c <;> decide
end V55
