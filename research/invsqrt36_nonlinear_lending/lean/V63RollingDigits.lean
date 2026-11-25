import Std
namespace V63

def bx (a b : Bool) : Bool := Bool.xor a b

theorem care_read (f x a : Bool) (h : f = true → x = false) :
    (f && bx x a) = (f && a) := by
  cases f
  · rfl
  · have hx := h rfl
    subst x
    cases a <;> decide

theorem rolling_update (x a b : Bool) :
    bx (bx x a) (bx a b) = bx x b := by
  cases x <;> cases a <;> cases b <;> decide

theorem rolling_restore (x a b : Bool) :
    bx (bx (bx x a) (bx a b)) b = x := by
  cases x <;> cases a <;> cases b <;> decide

theorem measured_product (m f a : Bool) :
    bx (m && (f && a)) (m && f && a) = false := by
  cases m <;> cases f <;> cases a <;> decide

theorem capacity36 (k : Nat) (hk : 1 ≤ k) (h : k ≤ 17) :
    k + 1 + 1 + (k-1) + (35-2*k) ≤ 36 := by
  omega
end V63
