import Std.Tactic.BVDecide
namespace WireFrameV8

-- Actual logical-to-physical map, written as an arbitrary function.
def swapIdx (a b q : Nat) : Nat := if q = a then b else if q = b then a else q
def rename (s : Nat → Bool) (p : Nat → Nat) : Nat → Bool := fun q => s (p q)
def swapState (s : Nat → Bool) (a b : Nat) : Nat → Bool := fun q => s (swapIdx a b q)

theorem swap_frame (s : Nat → Bool) (p : Nat → Nat) (a b : Nat) :
    swapState (rename s p) a b = rename s (fun q => p (swapIdx a b q)) := by rfl

-- Measurement result is arbitrary and independent. Renaming the measured
-- coordinate preserves its branch sign contribution and rotation read.
theorem hmr_frame (s : Nat → Bool) (p : Nat → Nat) (q : Nat) (active m phase : Bool) :
    Bool.xor phase (active && m && (rename s p) q) =
    Bool.xor phase (active && m && s (p q)) := by rfl

def reset (s : Nat → Bool) (q : Nat) (active : Bool) : Nat → Bool :=
  fun i => if i = q then s i && !active else s i

theorem reset_frame (s : Nat → Bool) (p : Nat → Nat) (q : Nat) (active : Bool)
    (inj : ∀ a b, p a = p b → a = b) :
    reset (rename s p) q active = rename (reset s (p q) active) p := by
  funext i
  by_cases hi : i = q
  · subst i
    simp [reset, rename]
  · have hn : p i ≠ p q := fun h => hi (inj i q h)
    simp [reset, rename, hi, hn]

def countPaid (g : List (List Nat)) : Nat := (g.filter (fun x => [48,49,50].contains (x.headD 0))).length
def within36 (g : List (List Nat)) : Bool := g.all (fun x => x.tail.all (fun q => q < 36))

-- Exact native V7B gates; conditional theorems assume the product decoder.
-- Reachability of decoder is established independently by full-domain BDD,
-- not by a Lean proof of the whole oracle.

def oldList6424 : List (List Nat) := [[49,11,12,15]]
def newList6424 : List (List Nat) := [[33,12,15],[33,14,15],[33,33,15],[33,35,15]]
theorem actual6424 (x11 x12 x14 x15 x33 x35 active phase : Bool)
    (h : (x11 && x12) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x12) x14) x33) x35)) :
    (Bool.xor x15 (active && x11 && x12), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x15 (active && x12)) (active && x14)) (active && x33)) (active && x35)), phase) := by
  bv_decide
theorem resources6424 : countPaid oldList6424 = 1 ∧ countPaid newList6424 = 0 ∧ within36 newList6424 = true := by decide

def oldList6594 : List (List Nat) := [[49,10,11,15]]
def newList6594 : List (List Nat) := [[33,11,15],[33,12,15],[33,14,15],[33,35,15]]
theorem actual6594 (x10 x11 x12 x14 x15 x35 active phase : Bool)
    (h : (x10 && x11) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x11) x12) x14) x35)) :
    (Bool.xor x15 (active && x10 && x11), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x15 (active && x11)) (active && x12)) (active && x14)) (active && x35)), phase) := by
  bv_decide
theorem resources6594 : countPaid oldList6594 = 1 ∧ countPaid newList6594 = 0 ∧ within36 newList6594 = true := by decide

def oldList8432 : List (List Nat) := [[49,6,27,15]]
def newList8432 : List (List Nat) := [[17,15],[33,6,15],[33,14,15],[33,27,15],[33,29,15],[33,35,15]]
theorem actual8432 (x6 x14 x15 x27 x29 x35 active phase : Bool)
    (h : (x6 && x27) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor true x6) x14) x27) x29) x35)) :
    (Bool.xor x15 (active && x6 && x27), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor x15 active) (active && x6)) (active && x14)) (active && x27)) (active && x29)) (active && x35)), phase) := by
  bv_decide
theorem resources8432 : countPaid oldList8432 = 1 ∧ countPaid newList8432 = 0 ∧ within36 newList8432 = true := by decide

def oldList8697 : List (List Nat) := [[49,3,16,18]]
def newList8697 : List (List Nat) := [[33,16,18],[33,17,18],[33,29,18],[33,35,18]]
theorem actual8697 (x3 x16 x17 x18 x29 x35 active phase : Bool)
    (h : (x3 && x16) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x16) x17) x29) x35)) :
    (Bool.xor x18 (active && x3 && x16), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x18 (active && x16)) (active && x17)) (active && x29)) (active && x35)), phase) := by
  bv_decide
theorem resources8697 : countPaid oldList8697 = 1 ∧ countPaid newList8697 = 0 ∧ within36 newList8697 = true := by decide

def oldList8767 : List (List Nat) := [[49,2,17,19]]
def newList8767 : List (List Nat) := [[33,17,19],[33,18,19],[33,29,19],[33,35,19]]
theorem actual8767 (x2 x17 x18 x19 x29 x35 active phase : Bool)
    (h : (x2 && x17) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x17) x18) x29) x35)) :
    (Bool.xor x19 (active && x2 && x17), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x19 (active && x17)) (active && x18)) (active && x29)) (active && x35)), phase) := by
  bv_decide
theorem resources8767 : countPaid oldList8767 = 1 ∧ countPaid newList8767 = 0 ∧ within36 newList8767 = true := by decide

def oldList8827 : List (List Nat) := [[49,1,18,20]]
def newList8827 : List (List Nat) := [[33,18,20],[33,19,20],[33,29,20],[33,35,20]]
theorem actual8827 (x1 x18 x19 x20 x29 x35 active phase : Bool)
    (h : (x1 && x18) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x18) x19) x29) x35)) :
    (Bool.xor x20 (active && x1 && x18), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x20 (active && x18)) (active && x19)) (active && x29)) (active && x35)), phase) := by
  bv_decide
theorem resources8827 : countPaid oldList8827 = 1 ∧ countPaid newList8827 = 0 ∧ within36 newList8827 = true := by decide

def oldList11005 : List (List Nat) := [[49,0,1,2]]
def newList11005 : List (List Nat) := [[33,26,2]]
theorem actual11005 (x0 x1 x2 x26 active phase : Bool)
    (h : (x0 && x1) = (Bool.xor false x26)) :
    (Bool.xor x2 (active && x0 && x1), phase) = ((Bool.xor x2 (active && x26)), phase) := by
  bv_decide
theorem resources11005 : countPaid oldList11005 = 1 ∧ countPaid newList11005 = 0 ∧ within36 newList11005 = true := by decide

def oldList17427 : List (List Nat) := [[49,18,26,0]]
def newList17427 : List (List Nat) := [[33,2,0],[33,17,0],[33,18,0],[33,29,0]]
theorem actual17427 (x0 x2 x17 x18 x26 x29 active phase : Bool)
    (h : (x18 && x26) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x2) x17) x18) x29)) :
    (Bool.xor x0 (active && x18 && x26), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x0 (active && x2)) (active && x17)) (active && x18)) (active && x29)), phase) := by
  bv_decide
theorem resources17427 : countPaid oldList17427 = 1 ∧ countPaid newList17427 = 0 ∧ within36 newList17427 = true := by decide

end WireFrameV8
