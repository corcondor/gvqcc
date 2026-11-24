import Std.Tactic.BVDecide
namespace PeerV8
def countPaid (g : List (List Nat)) : Nat := (g.filter (fun x => [48,49,50].contains (x.headD 0))).length
def within36 (g : List (List Nat)) : Bool := g.all (fun x => x.tail.all (fun q => q < 36))
-- Actual peer91-frame native replacement. Reachability hypothesis
-- is established independently by full-domain BDD, not by this lemma.
def old5882 : List (List Nat) := [[49,14,33,20]]
def new5882 : List (List Nat) := [[33,11,20],[33,12,20],[33,21,20],[33,33,20]]
theorem actual5882 (x11 x12 x14 x20 x21 x33 phase : Bool)
    (h : (x14 && x33) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x11) x12) x21) x33)) :
    (Bool.xor x20 (x14 && x33), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x20 x11) x12) x21) x33), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources5882 : countPaid old5882 = 1 ∧ countPaid new5882 = 0 ∧ within36 new5882 = true := by decide

def old6079 : List (List Nat) := [[49,14,11,15]]
def new6079 : List (List Nat) := [[33,10,15],[33,11,15],[33,12,15],[33,35,15]]
theorem actual6079 (x10 x11 x12 x14 x15 x35 phase : Bool)
    (h : (x14 && x11) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x10) x11) x12) x35)) :
    (Bool.xor x15 (x14 && x11), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x15 x10) x11) x12) x35), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources6079 : countPaid old6079 = 1 ∧ countPaid new6079 = 0 ∧ within36 new6079 = true := by decide

def old7916 : List (List Nat) := [[49,6,27,15]]
def new7916 : List (List Nat) := [[17,15],[33,6,15],[33,14,15],[33,27,15],[33,29,15],[33,35,15]]
theorem actual7916 (x6 x14 x15 x27 x29 x35 phase : Bool)
    (h : (x6 && x27) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor true x6) x14) x27) x29) x35)) :
    (Bool.xor x15 (x6 && x27), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor (Bool.xor x15 true) x6) x14) x27) x29) x35), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources7916 : countPaid old7916 = 1 ∧ countPaid new7916 = 0 ∧ within36 new7916 = true := by decide

def old8179 : List (List Nat) := [[49,3,16,21]]
def new8179 : List (List Nat) := [[33,15,21],[33,16,21],[33,17,21],[33,35,21]]
theorem actual8179 (x3 x15 x16 x17 x21 x35 phase : Bool)
    (h : (x3 && x16) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x15) x16) x17) x35)) :
    (Bool.xor x21 (x3 && x16), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x21 x15) x16) x17) x35), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources8179 : countPaid old8179 = 1 ∧ countPaid new8179 = 0 ∧ within36 new8179 = true := by decide

def old8251 : List (List Nat) := [[49,2,17,19]]
def new8251 : List (List Nat) := [[33,17,19],[33,18,19],[33,29,19],[33,35,19]]
theorem actual8251 (x2 x17 x18 x19 x29 x35 phase : Bool)
    (h : (x2 && x17) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x17) x18) x29) x35)) :
    (Bool.xor x19 (x2 && x17), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x19 x17) x18) x29) x35), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources8251 : countPaid old8251 = 1 ∧ countPaid new8251 = 0 ∧ within36 new8251 = true := by decide

def old8311 : List (List Nat) := [[49,1,18,20]]
def new8311 : List (List Nat) := [[33,18,20],[33,19,20],[33,29,20],[33,35,20]]
theorem actual8311 (x1 x18 x19 x20 x29 x35 phase : Bool)
    (h : (x1 && x18) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x18) x19) x29) x35)) :
    (Bool.xor x20 (x1 && x18), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x20 x18) x19) x29) x35), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources8311 : countPaid old8311 = 1 ∧ countPaid new8311 = 0 ∧ within36 new8311 = true := by decide

def old10293 : List (List Nat) := [[49,0,1,2]]
def new10293 : List (List Nat) := [[33,26,2]]
theorem actual10293 (x0 x1 x2 x26 phase : Bool)
    (h : (x0 && x1) = (Bool.xor false x26)) :
    (Bool.xor x2 (x0 && x1), phase) = ((Bool.xor x2 x26), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources10293 : countPaid old10293 = 1 ∧ countPaid new10293 = 0 ∧ within36 new10293 = true := by decide

def old15846 : List (List Nat) := [[49,4,7,9]]
def new15846 : List (List Nat) := [[33,1,9],[33,4,9],[33,8,9],[33,32,9]]
theorem actual15846 (x1 x4 x7 x8 x9 x32 phase : Bool)
    (h : (x4 && x7) = (Bool.xor (Bool.xor (Bool.xor (Bool.xor false x1) x4) x8) x32)) :
    (Bool.xor x9 (x4 && x7), phase) = ((Bool.xor (Bool.xor (Bool.xor (Bool.xor x9 x1) x4) x8) x32), phase) := by
  apply Prod.ext <;> simp only [Prod.fst, Prod.snd] <;> bv_decide
theorem resources15846 : countPaid old15846 = 1 ∧ countPaid new15846 = 0 ∧ within36 new15846 = true := by decide

end PeerV8
