import Std.Tactic.BVDecide
set_option maxRecDepth 8192
namespace RankHubV7B
def countPaid (g : List (List Nat)) : Nat := (g.filter (fun x => [48,49,50].contains (x.headD 0))).length
def within36 (g : List (List Nat)) : Bool := g.all (fun x => x.tail.all (fun q => q < 36))
-- GF(2) phase factorization, with an arbitrary guard and incident phase.
theorem shared_factor (a b c d active phase : Bool) :
    Bool.xor (Bool.xor phase (active && a && b && c)) (active && a && b && d) =
    Bool.xor phase (active && a && b && Bool.xor c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases active <;> cases phase <;> decide
theorem rank_pivot (a b u v : Bool) :
    Bool.xor (Bool.xor (Bool.xor (a && b) (a && v)) (u && b)) (u && v) =
    (Bool.xor a u && Bool.xor b v) := by
  cases a <;> cases b <;> cases u <;> cases v <;> decide
-- Exact native gate subsequences, guard stripped to a common Boolean active.
def oldList_union17222 : List (List Nat) := [[32,0,6],[48,0,1,6],[32,0,18],[48,0,1,18],[32,0,22],[48,0,1,22],[32,0,25],[48,0,1,25],[32,0,30],[48,0,1,30],[32,0,31],[48,0,1,31],[32,0,33],[48,0,1,33],[32,0,34],[48,0,1,34]]
def newList_union17222 : List (List Nat) := [[33,18,6],[33,22,6],[33,25,6],[33,30,6],[33,31,6],[33,33,6],[33,34,6],[48,1,6,0],[32,6,0],[33,34,6],[33,33,6],[33,31,6],[33,30,6],[33,25,6],[33,22,6],[33,18,6]]
def old_union17222 (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 active phase : Bool) : List Bool :=
  let phase1 := Bool.xor phase (active && x0 && x6)
  let phase2 := Bool.xor phase1 (active && x0 && x1 && x6)
  let phase3 := Bool.xor phase2 (active && x0 && x18)
  let phase4 := Bool.xor phase3 (active && x0 && x1 && x18)
  let phase5 := Bool.xor phase4 (active && x0 && x22)
  let phase6 := Bool.xor phase5 (active && x0 && x1 && x22)
  let phase7 := Bool.xor phase6 (active && x0 && x25)
  let phase8 := Bool.xor phase7 (active && x0 && x1 && x25)
  let phase9 := Bool.xor phase8 (active && x0 && x30)
  let phase10 := Bool.xor phase9 (active && x0 && x1 && x30)
  let phase11 := Bool.xor phase10 (active && x0 && x31)
  let phase12 := Bool.xor phase11 (active && x0 && x1 && x31)
  let phase13 := Bool.xor phase12 (active && x0 && x33)
  let phase14 := Bool.xor phase13 (active && x0 && x1 && x33)
  let phase15 := Bool.xor phase14 (active && x0 && x34)
  let phase16 := Bool.xor phase15 (active && x0 && x1 && x34)
  [x0, x1, x6, x18, x22, x25, x30, x31, x33, x34, phase16]

def new_union17222 (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 active phase : Bool) : List Bool :=
  let q6_1 := Bool.xor x6 (active && x18)
  let q6_2 := Bool.xor q6_1 (active && x22)
  let q6_3 := Bool.xor q6_2 (active && x25)
  let q6_4 := Bool.xor q6_3 (active && x30)
  let q6_5 := Bool.xor q6_4 (active && x31)
  let q6_6 := Bool.xor q6_5 (active && x33)
  let q6_7 := Bool.xor q6_6 (active && x34)
  let phase1 := Bool.xor phase (active && x1 && q6_7 && x0)
  let phase2 := Bool.xor phase1 (active && q6_7 && x0)
  let q6_8 := Bool.xor q6_7 (active && x34)
  let q6_9 := Bool.xor q6_8 (active && x33)
  let q6_10 := Bool.xor q6_9 (active && x31)
  let q6_11 := Bool.xor q6_10 (active && x30)
  let q6_12 := Bool.xor q6_11 (active && x25)
  let q6_13 := Bool.xor q6_12 (active && x22)
  let q6_14 := Bool.xor q6_13 (active && x18)
  [x0, x1, q6_14, x18, x22, x25, x30, x31, x33, x34, phase2]

theorem actual_union17222 (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 active phase : Bool) : old_union17222 x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 active phase = new_union17222 x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 active phase := by
  simp [old_union17222, new_union17222] <;> bv_decide

theorem resource_union17222 : countPaid oldList_union17222 = 8 ∧ countPaid newList_union17222 = 1 ∧ within36 newList_union17222 = true := by decide

-- Exact native gate subsequences, guard stripped to a common Boolean active.
def oldList_union35272 : List (List Nat) := [[32,17,20],[48,17,19,20],[48,17,20,25],[32,19,20],[48,17,19,20],[48,19,20,25],[48,17,20,21],[48,19,20,21],[48,20,21,25]]
def newList_union35272 : List (List Nat) := [[33,17,21],[33,19,21],[33,17,25],[33,19,25],[48,20,21,25],[33,19,25],[33,17,25],[33,19,21],[33,17,21]]
def old_union35272 (x17 x19 x20 x21 x25 active phase : Bool) : List Bool :=
  let phase1 := Bool.xor phase (active && x17 && x20)
  let phase2 := Bool.xor phase1 (active && x17 && x19 && x20)
  let phase3 := Bool.xor phase2 (active && x17 && x20 && x25)
  let phase4 := Bool.xor phase3 (active && x19 && x20)
  let phase5 := Bool.xor phase4 (active && x17 && x19 && x20)
  let phase6 := Bool.xor phase5 (active && x19 && x20 && x25)
  let phase7 := Bool.xor phase6 (active && x17 && x20 && x21)
  let phase8 := Bool.xor phase7 (active && x19 && x20 && x21)
  let phase9 := Bool.xor phase8 (active && x20 && x21 && x25)
  [x17, x19, x20, x21, x25, phase9]

def new_union35272 (x17 x19 x20 x21 x25 active phase : Bool) : List Bool :=
  let q21_1 := Bool.xor x21 (active && x17)
  let q21_2 := Bool.xor q21_1 (active && x19)
  let q25_1 := Bool.xor x25 (active && x17)
  let q25_2 := Bool.xor q25_1 (active && x19)
  let phase1 := Bool.xor phase (active && x20 && q21_2 && q25_2)
  let q25_3 := Bool.xor q25_2 (active && x19)
  let q25_4 := Bool.xor q25_3 (active && x17)
  let q21_3 := Bool.xor q21_2 (active && x19)
  let q21_4 := Bool.xor q21_3 (active && x17)
  [x17, x19, x20, q21_4, q25_4, phase1]

theorem actual_union35272 (x17 x19 x20 x21 x25 active phase : Bool) : old_union35272 x17 x19 x20 x21 x25 active phase = new_union35272 x17 x19 x20 x21 x25 active phase := by
  simp [old_union35272, new_union35272] <;> bv_decide

theorem resource_union35272 : countPaid oldList_union35272 = 7 ∧ countPaid newList_union35272 = 1 ∧ within36 newList_union35272 = true := by decide

-- Exact native gate subsequences, guard stripped to a common Boolean active.
def oldList_peer35216 : List (List Nat) := [[32,25,35],[48,19,20,35],[48,20,25,35]]
def newList_peer35216 : List (List Nat) := [[33,25,19],[48,20,35,19],[33,25,19],[32,25,35]]
def old_peer35216 (x19 x20 x25 x35 active phase : Bool) : List Bool :=
  let phase1 := Bool.xor phase (active && x25 && x35)
  let phase2 := Bool.xor phase1 (active && x19 && x20 && x35)
  let phase3 := Bool.xor phase2 (active && x20 && x25 && x35)
  [x19, x20, x25, x35, phase3]

def new_peer35216 (x19 x20 x25 x35 active phase : Bool) : List Bool :=
  let q19_1 := Bool.xor x19 (active && x25)
  let phase1 := Bool.xor phase (active && x20 && x35 && q19_1)
  let q19_2 := Bool.xor q19_1 (active && x25)
  let phase2 := Bool.xor phase1 (active && x25 && x35)
  [q19_2, x20, x25, x35, phase2]

theorem actual_peer35216 (x19 x20 x25 x35 active phase : Bool) : old_peer35216 x19 x20 x25 x35 active phase = new_peer35216 x19 x20 x25 x35 active phase := by
  simp [old_peer35216, new_peer35216] <;> bv_decide

theorem resource_peer35216 : countPaid oldList_peer35216 = 2 ∧ countPaid newList_peer35216 = 1 ∧ within36 newList_peer35216 = true := by decide

-- Exact native gate subsequences, guard stripped to a common Boolean active.
def oldList_peer35219 : List (List Nat) := [[32,20,35],[48,19,20,35],[48,20,25,35],[32,33,35]]
def newList_peer35219 : List (List Nat) := [[33,25,19],[48,20,35,19],[33,25,19],[32,20,35],[32,33,35]]
def old_peer35219 (x19 x20 x25 x33 x35 active phase : Bool) : List Bool :=
  let phase1 := Bool.xor phase (active && x20 && x35)
  let phase2 := Bool.xor phase1 (active && x19 && x20 && x35)
  let phase3 := Bool.xor phase2 (active && x20 && x25 && x35)
  let phase4 := Bool.xor phase3 (active && x33 && x35)
  [x19, x20, x25, x33, x35, phase4]

def new_peer35219 (x19 x20 x25 x33 x35 active phase : Bool) : List Bool :=
  let q19_1 := Bool.xor x19 (active && x25)
  let phase1 := Bool.xor phase (active && x20 && x35 && q19_1)
  let q19_2 := Bool.xor q19_1 (active && x25)
  let phase2 := Bool.xor phase1 (active && x20 && x35)
  let phase3 := Bool.xor phase2 (active && x33 && x35)
  [q19_2, x20, x25, x33, x35, phase3]

theorem actual_peer35219 (x19 x20 x25 x33 x35 active phase : Bool) : old_peer35219 x19 x20 x25 x33 x35 active phase = new_peer35219 x19 x20 x25 x33 x35 active phase := by
  simp [old_peer35219, new_peer35219] <;> bv_decide

theorem resource_peer35219 : countPaid oldList_peer35219 = 2 ∧ countPaid newList_peer35219 = 1 ∧ within36 newList_peer35219 = true := by decide

-- Exact native gate subsequences, guard stripped to a common Boolean active.
def oldList_peer35312 : List (List Nat) := [[48,17,20,21],[48,19,20,21],[48,20,21,25]]
def newList_peer35312 : List (List Nat) := [[33,19,17],[33,25,17],[48,20,21,17],[33,25,17],[33,19,17]]
def old_peer35312 (x17 x19 x20 x21 x25 active phase : Bool) : List Bool :=
  let phase1 := Bool.xor phase (active && x17 && x20 && x21)
  let phase2 := Bool.xor phase1 (active && x19 && x20 && x21)
  let phase3 := Bool.xor phase2 (active && x20 && x21 && x25)
  [x17, x19, x20, x21, x25, phase3]

def new_peer35312 (x17 x19 x20 x21 x25 active phase : Bool) : List Bool :=
  let q17_1 := Bool.xor x17 (active && x19)
  let q17_2 := Bool.xor q17_1 (active && x25)
  let phase1 := Bool.xor phase (active && x20 && x21 && q17_2)
  let q17_3 := Bool.xor q17_2 (active && x25)
  let q17_4 := Bool.xor q17_3 (active && x19)
  [q17_4, x19, x20, x21, x25, phase1]

theorem actual_peer35312 (x17 x19 x20 x21 x25 active phase : Bool) : old_peer35312 x17 x19 x20 x21 x25 active phase = new_peer35312 x17 x19 x20 x21 x25 active phase := by
  simp [old_peer35312, new_peer35312] <;> bv_decide

theorem resource_peer35312 : countPaid oldList_peer35312 = 3 ∧ countPaid newList_peer35312 = 1 ∧ within36 newList_peer35312 = true := by decide

-- Exact native gate subsequences, guard stripped to a common Boolean active.
def oldList_peer35329 : List (List Nat) := [[48,16,17,20],[48,16,19,20],[48,16,20,25]]
def newList_peer35329 : List (List Nat) := [[33,19,17],[33,25,17],[48,16,20,17],[33,25,17],[33,19,17]]
def old_peer35329 (x16 x17 x19 x20 x25 active phase : Bool) : List Bool :=
  let phase1 := Bool.xor phase (active && x16 && x17 && x20)
  let phase2 := Bool.xor phase1 (active && x16 && x19 && x20)
  let phase3 := Bool.xor phase2 (active && x16 && x20 && x25)
  [x16, x17, x19, x20, x25, phase3]

def new_peer35329 (x16 x17 x19 x20 x25 active phase : Bool) : List Bool :=
  let q17_1 := Bool.xor x17 (active && x19)
  let q17_2 := Bool.xor q17_1 (active && x25)
  let phase1 := Bool.xor phase (active && x16 && x20 && q17_2)
  let q17_3 := Bool.xor q17_2 (active && x25)
  let q17_4 := Bool.xor q17_3 (active && x19)
  [x16, q17_4, x19, x20, x25, phase1]

theorem actual_peer35329 (x16 x17 x19 x20 x25 active phase : Bool) : old_peer35329 x16 x17 x19 x20 x25 active phase = new_peer35329 x16 x17 x19 x20 x25 active phase := by
  simp [old_peer35329, new_peer35329] <;> bv_decide

theorem resource_peer35329 : countPaid oldList_peer35329 = 3 ∧ countPaid newList_peer35329 = 1 ∧ within36 newList_peer35329 = true := by decide

end RankHubV7B
