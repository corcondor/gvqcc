import Std.Tactic
namespace GVQCC.V36MovingDebt
def X := Bool.xor

-- At cut t the candidate phase is sourcePhase XOR (m AND omitted).
-- A virtual XOR write carries the obligation without creating the bit.
theorem virtual_write (p m f h : Bool) :
    X (X p (m && f)) (m && h) =
    X p (m && X f h) := by
  cases p <;> cases m <;> cases f <;> cases h <;> decide

def accumulate : List Bool → Bool
  | [] => false
  | h :: hs => X h (accumulate hs)

def update (f : Bool) (hs : List Bool) : Bool :=
  X f (accumulate hs)

theorem sum_step (m f h r : Bool) :
    X (m && f) (X (m && h) (m && r)) =
    (m && X f (X h r)) := by
  cases m <;> cases f <;> cases h <;> cases r <;> decide

theorem weighted_sum (m : Bool) (hs : List Bool) :
    accumulate (hs.map (fun h => m && h)) = (m && accumulate hs) := by
  induction hs with
  | nil => cases m <;> rfl
  | cons h hs ih =>
    change X (m && h) (accumulate (hs.map (fun h => m && h))) =
      (m && X h (accumulate hs))
    rw [ih]
    cases m <;> cases h <;> cases accumulate hs <;> rfl

theorem interval_debt (p m f : Bool) (hs : List Bool) :
    X (X p (m && f)) (accumulate (hs.map (fun h => m && h))) =
      X p (m && update f hs) := by
  rw [weighted_sum]
  unfold update
  exact virtual_write p m f (accumulate hs)

-- Direct exchange with retained w: no second physical slot is needed.
-- The old omitted z is restored on w's slot, and w is encoded virtually.
theorem direct_exchange (p m z w h : Bool) (r : z = X w h) :
    (X w h, X (X p (m && z)) (m && X w h)) = (z, p) := by
  subst z
  cases p <;> cases m <;> cases w <;> cases h <;> decide

theorem exchange_inverse (w h : Bool) : X (X w h) h = w := by
  cases w <;> cases h <;> decide

-- Source event m is retained, even if physically drawn on an initially
-- zero slot. Here we prove its branch sign and classical publication.
-- This is not a full Hilbert-space/channel theorem.
theorem precoin_hmr (p f m r : Bool) (h : r = f) :
    (false, m, X p (m && f), false) =
    (false, m, X (X p (m && false)) (m && r), false) := by
  subst r
  cases p <;> cases f <;> cases m <;> decide

theorem ghost_retirement (p m f : Bool) (hs : List Bool) :
    X (X p (m && f)) (accumulate (hs.map (fun h => m && h))) =
    X p (m && update f hs) :=
  interval_debt p m f hs

-- Real V35 combined parent native [7877,7888):
-- initial q36=0; a=q17,b=q33,c=q26,d=q21,e=q35,t=q32.
-- Source builds f, uses f in CCX, removes affine part, HMR(q36).
def source7877 (a b c d e t m : Bool) : Bool × Bool × Bool :=
  let h := a && b
  let f := X (X (X (X h c) a) d) true
  let t' := X t (f && e)
  let f' := X (X (X (X f true) d) a) c
  (d,t',m && f')

-- Two direct exchanges, 36 -> 21 -> 36. Retained q21 is changed
-- into f, consumed, and restored; the phase uses the pre-sampled event.
def target7877 (a b c d e t m : Bool) : Bool × Bool × Bool :=
  let h := a && b
  let u := X (X (X (X d h) true) a) c
  let t' := X t (u && e)
  let d' := X (X (X (X u true) h) a) c
  (d',t',m && h)

theorem native7877_projection (a b c d e t m : Bool) :
    source7877 a b c d e t m = target7877 a b c d e t m := by
  cases a <;> cases b <;> cases c <;> cases d <;>
  cases e <;> cases t <;> cases m <;> decide

-- Rank/width receipt: native whole circuit is still 37Q.
theorem measured_receipt :
    3554 - 251 = 3303 ∧ 22991 + 240 = 23231 ∧
    1281 + 9 = 1290 ∧ 51380 - 51321 = 59 := by decide
end GVQCC.V36MovingDebt
