import Std.Tactic
namespace GVQCC.V40

def X := Bool.xor

-- Toggle detection for an arbitrary dirty bit.  The borrowed bit is
-- restored, and both the data update and the relative phase are exact.
theorem dirty_pair (r h t g l j m : Bool) :
    (X (X r h) h,
     X (X t (X r h)) r,
     X (X (X (g && r && t) (g && X r h && t))
          (X (j && r && l) (j && X r h && l))) (m && h)) =
    (r, X t h, X (X (g && h && t) (j && h && l)) (m && h)) := by
  cases r <;> cases h <;> cases t <;> cases g <;> cases l <;> cases j <;> cases m <;> decide

-- This projected certificate follows the data and phase of the actual
-- native 23771..23782 replacement (h=a*b, l is the seven-read parity).
theorem native23771 (r a b t g l j m : Bool) :
    (X (X r (a && b)) (a && b),
     X (X t (X r (a && b))) r,
     X (X (X (g && r && t) (g && X r (a && b) && t))
          (X (j && r && l) (j && X r (a && b) && l))) (m && a && b)) =
    (r, X t (a && b), X (X (g && a && b && t) (j && a && b && l)) (m && a && b)) := by
  cases r <;> cases a <;> cases b <;> cases t <;> cases g <;> cases l <;> cases j <;> cases m <;> decide

-- Actual 36126..36145 source phase observation cancels its product
-- after the carry update.  This is not the entire reachable-state proof.
theorem carry_debt (a b c m : Bool) :
    (m && X (a && b) (X (X a (a && b)) c)) =
    X (m && a) (m && c) := by
  cases a <;> cases b <;> cases c <;> cases m <;> decide

-- Pre-sampled zero-wire HMR contributes zero phase; pay the original
-- event's phase on the retained controls without measuring a data wire.
theorem presampled (p m a b : Bool) :
    X (X p (m && false)) (m && a && b) =
    X p (m && (a && b)) := by
  cases p <;> cases m <;> cases a <;> cases b <;> decide

-- Restricted obstruction: a cubic phase in independent a,b,t is not
-- quadratic. The shear t'=t XOR ab preserves the degree-two space
-- on these three coordinates (because Boolean squares are idempotent).
theorem shear_linear (a b t : Bool) :
    X t (a && b) = X t (a && b) := rfl

theorem shear_product_a (a b t : Bool) :
    (a && X t (a && b)) = X (a && t) (a && b) := by
  cases a <;> cases b <;> cases t <;> decide

theorem shear_product_b (a b t : Bool) :
    (b && X t (a && b)) = X (b && t) (a && b) := by
  cases a <;> cases b <;> cases t <;> decide

def q (c0 c1 c2 c3 c4 c5 c6 a b t : Bool) : Bool :=
  X (X (X c0 (c1 && a)) (X (c2 && b) (c3 && t)))
    (X (c4 && a && b) (X (c5 && a && t) (c6 && b && t)))

def parity8 (f : Bool → Bool → Bool → Bool) : Bool :=
  X (X (X (f false false false) (f false false true))
       (X (f false true false) (f false true true)))
    (X (X (f true false false) (f true false true))
       (X (f true true false) (f true true true)))

theorem degree2_even (c0 c1 c2 c3 c4 c5 c6 : Bool) :
    parity8 (q c0 c1 c2 c3 c4 c5 c6) = false := by
  cases c0 <;> cases c1 <;> cases c2 <;> cases c3 <;> cases c4 <;> cases c5 <;> cases c6 <;> decide

theorem cubic_odd : parity8 (fun a b t => a && b && t) = true := by decide

theorem receipts : 23127 - 32 = 23095 ∧ 23095 + 32 = 23127 ∧
    3239 - 28 = 3211 ∧ 41935 + 10 + 22 = 41967 := by decide

end GVQCC.V40
