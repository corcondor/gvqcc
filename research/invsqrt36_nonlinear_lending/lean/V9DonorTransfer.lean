import Std.Tactic.BVDecide
namespace V9DonorTransfer
def paid (g : List (List Nat)) : Nat := (g.filter (fun x => [48,49,50].contains (x.headD 0))).length
def within36 (g : List (List Nat)) : Bool := g.all (fun x => x.tail.all (fun q => q < 36))
-- Reachability separately verified by exact BDD.

def old5867 : List (List Nat) := [[49,16,33,3]]
def new5867 : List (List Nat) := [[33,11,3],[33,12,3],[33,24,3],[33,33,3]]
theorem actual5867 (x3 x11 x12 x16 x24 x33 phase : Bool)
    (h : (x16 && x33) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x11) x12) x24) x33)) :
    (Bool.xor x3 (x16 && x33), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x3 x11) x12) x24) x33), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources5867 : paid old5867 = 1 ∧ paid new5867 = 0 ∧ within36 new5867 = true := by decide

def old6026 : List (List Nat) := [[49,24,16,3]]
def new6026 : List (List Nat) := [[33,10,3],[33,16,3],[33,33,3],[33,12,3]]
theorem actual6026 (x3 x10 x12 x16 x24 x33 phase : Bool)
    (h : (x24 && x16) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x10) x16) x33) x12)) :
    (Bool.xor x3 (x24 && x16), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x3 x10) x16) x33) x12), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources6026 : paid old6026 = 1 ∧ paid new6026 = 0 ∧ within36 new6026 = true := by decide

def old7851 : List (List Nat) := [[49,19,7,3]]
def new7851 : List (List Nat) := [[17,3],[33,19,3],[33,10,3],[33,7,3],[33,13,3],[33,33,3]]
theorem actual7851 (x3 x7 x10 x13 x19 x33 phase : Bool)
    (h : (x19 && x7) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor false true) x19) x10) x7) x13) x33)) :
    (Bool.xor x3 (x19 && x7), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor x3 true) x19) x10) x7) x13) x33), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources7851 : paid old7851 = 1 ∧ paid new7851 = 0 ∧ within36 new7851 = true := by decide

def old8105 : List (List Nat) := [[49,25,6,34]]
def new8105 : List (List Nat) := [[33,3,34],[33,6,34],[33,20,34],[33,33,34]]
theorem actual8105 (x3 x6 x20 x25 x33 x34 phase : Bool)
    (h : (x25 && x6) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x3) x6) x20) x33)) :
    (Bool.xor x34 (x25 && x6), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x34 x3) x6) x20) x33), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources8105 : paid old8105 = 1 ∧ paid new8105 = 0 ∧ within36 new8105 = true := by decide

def old8174 : List (List Nat) := [[49,31,20,8]]
def new8174 : List (List Nat) := [[33,20,8],[33,34,8],[33,3,8],[33,33,8]]
theorem actual8174 (x3 x8 x20 x31 x33 x34 phase : Bool)
    (h : (x31 && x20) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x20) x34) x3) x33)) :
    (Bool.xor x8 (x31 && x20), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x8 x20) x34) x3) x33), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources8174 : paid old8174 = 1 ∧ paid new8174 = 0 ∧ within36 new8174 = true := by decide

def old8233 : List (List Nat) := [[49,9,34,15]]
def new8233 : List (List Nat) := [[33,34,15],[33,8,15],[33,33,15],[33,3,15]]
theorem actual8233 (x3 x8 x9 x15 x33 x34 phase : Bool)
    (h : (x9 && x34) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x34) x8) x33) x3)) :
    (Bool.xor x15 (x9 && x34), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x15 x34) x8) x33) x3), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources8233 : paid old8233 = 1 ∧ paid new8233 = 0 ∧ within36 new8233 = true := by decide

def old9664 : List (List Nat) := [[49,26,27,30]]
def new9664 : List (List Nat) := [[33,33,30]]
theorem actual9664 (x26 x27 x30 x33 phase : Bool)
    (h : (x26 && x27) = (Bool.xor false x33)) :
    (Bool.xor x30 (x26 && x27), phase) = ((Bool.xor x30 x33), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources9664 : paid old9664 = 1 ∧ paid new9664 = 0 ∧ within36 new9664 = true := by decide

def old13598 : List (List Nat) := [[49,4,0,29]]
def new13598 : List (List Nat) := [[33,27,29],[33,4,29],[33,19,29],[33,3,29]]
theorem actual13598 (x0 x3 x4 x19 x27 x29 phase : Bool)
    (h : (x4 && x0) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x27) x4) x19) x3)) :
    (Bool.xor x29 (x4 && x0), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x29 x27) x4) x19) x3), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources13598 : paid old13598 = 1 ∧ paid new13598 = 0 ∧ within36 new13598 = true := by decide

end V9DonorTransfer
