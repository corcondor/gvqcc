import Std.Tactic.BVDecide
set_option maxRecDepth 8192
/-! V6 guarded atlas: Boolean branch, phase and actual gate-list certificates.
   This is a basis-state/sign model, not a full quantum oracle theorem.
   The source ABI and reachability are certified separately by exact BDD. -/
namespace GVQCCV6
def countPaid (g : List (List Nat)) : Nat :=
  (g.filter (fun x => [48,49,50].contains (x.headD 0 % 128))).length
def arity (n : Nat) : Nat :=
  if [17,16,80,144].contains n then 1 else
  if [33,34,32,160].contains n then 2 else
  if [49,50,48].contains n then 3 else 0
def within36 (g : List (List Nat)) : Bool :=
  g.all (fun o => (o.tail.take (arity (o.headD 0))).all (fun q => q < 36))
theorem guarded_join (active old new replacement : Bool)
    (h : active = true → new = replacement) :
    (if active then new else old) = (if active then replacement else old) := by
  cases active
  · rfl
  · exact h rfl
theorem measured_chart_phase (phase stored decoder m : Bool) (h : stored = decoder) :
    Bool.xor (Bool.xor phase (stored && m)) (decoder && m) = phase := by
  subst stored
  cases phase <;> cases decoder <;> cases m <;> decide
theorem latent_write_only (old f g observed : Bool) :
    (observed, Bool.xor (Bool.xor old f) g) =
    (observed, Bool.xor old (Bool.xor f g)) := by
  cases old <;> cases f <;> cases g <;> rfl

-- Actual source operations [21910,21956); omitted entry and exit q29=0.
-- Both IF arms, all initial retained wires, all HMR outcomes, arbitrary phase.
def source21910 (x2 x3 x17 x19 x22 x23 x30 x33 x36 c481 c482 c483 m0 m1 phase : Bool) : List Bool :=
  let q2_1 := x2
  let q3_1 := x3
  let q17_1 := x17
  let q19_1 := x19
  let q22_1 := x22
  let q23_1 := x23
  let q29_1 := false
  let q30_1 := x30
  let q33_1 := x33
  let q36_1 := x36
  let q33_2 := (Bool.xor q33_1 (c482 && q19_1))
  let q23_2 := (Bool.xor q23_1 (c482 && q19_1))
  let q33_3 := (Bool.xor q33_2 c482)
  let q29_2 := (Bool.xor q29_1 (c482 && (q23_2 && q33_3)))
  let p_1 := (Bool.xor phase ((c482 && c481) && q17_1))
  let q29_3 := (Bool.xor q29_2 (c482 && q19_1))
  let p_2 := (Bool.xor p_1 ((c482 && c481) && q29_3))
  let p_3 := (Bool.xor p_2 (((c482 && c481) && q2_1) && q17_1))
  let p_4 := (Bool.xor p_3 (((c482 && c481) && q17_1) && q29_3))
  let p_5 := (Bool.xor p_4 (((c482 && c481) && q2_1) && q29_3))
  let q17_2 := (Bool.xor q17_1 (c482 && q29_3))
  let q29_4 := (Bool.xor q29_3 (c482 && q2_1))
  let q29_5 := (Bool.xor q29_4 c482)
  let q30_2 := (Bool.xor q30_1 (c482 && (q17_2 && q29_5)))
  let p_6 := (Bool.xor p_5 (c482 && q22_1))
  let q30_3 := (Bool.xor q30_2 (c482 && q29_5))
  let q30_4 := (Bool.xor q30_3 (c482 && q2_1))
  let q30_5 := (Bool.xor q30_4 c482)
  let p_7 := (Bool.xor p_6 (c482 && q30_5))
  let p_8 := (Bool.xor p_7 ((c482 && q3_1) && q22_1))
  let p_9 := (Bool.xor p_8 ((c482 && q22_1) && q30_5))
  let p_10 := (Bool.xor p_9 ((c482 && q3_1) && q30_5))
  let p_11 := (Bool.xor p_10 (c482 && (q30_5 && m0)))
  let q30_6 := (q30_5 && (Bool.not c482))
  let c483_1 := (if c482 then m0 else c483)
  let q29_6 := (Bool.xor q29_5 (c482 && q17_2))
  let q29_7 := (Bool.xor q29_6 (c482 && q2_1))
  let q29_8 := (Bool.xor q29_7 c482)
  let p_12 := (Bool.xor p_11 ((c482 && c483_1) && q29_8))
  let q29_9 := (Bool.xor q29_8 (c482 && q17_2))
  let p_13 := (Bool.xor p_12 ((c482 && c483_1) && q29_9))
  let q29_10 := (Bool.xor q29_9 (c482 && q17_2))
  let p_14 := (Bool.xor p_13 (((c482 && c483_1) && q2_1) && q29_10))
  let q17_3 := (Bool.xor q17_2 (c482 && q29_10))
  let p_15 := (Bool.xor p_14 (((c482 && c483_1) && q17_3) && q29_10))
  let p_16 := (Bool.xor p_15 (((c482 && c483_1) && q2_1) && q17_3))
  let p_17 := (Bool.xor p_16 (c482 && (q17_3 && m1)))
  let q17_4 := (q17_3 && (Bool.not c482))
  let c483_2 := (if c482 then m1 else c483_1)
  let q23_3 := (Bool.xor q23_2 (c482 && q19_1))
  let p_18 := (Bool.xor p_17 ((c482 && c483_2) && q23_3))
  let p_19 := (Bool.xor p_18 ((c482 && c483_2) && q19_1))
  let q33_4 := (Bool.xor q33_3 (c482 && q19_1))
  let q33_5 := (Bool.xor q33_4 c482)
  let p_20 := (Bool.xor p_19 (((c482 && c483_2) && q23_3) && q33_5))
  let p_21 := (Bool.xor p_20 (((c482 && c483_2) && q19_1) && q23_3))
  let p_22 := (Bool.xor p_21 (((c482 && c483_2) && q19_1) && q33_5))
  let q29_11 := (if c482 then q17_4 else q29_10)
  let q17_5 := (if c482 then q29_10 else q17_4)
  [q2_1, q3_1, q17_5, q19_1, q22_1, q23_3, q29_11, q30_6, q33_5, q36_1, c481, c482, c483_2, p_22]

def candidate21910 (x2 x3 x17 x19 x22 x23 x30 x33 x36 c481 c482 c483 m0 m1 phase : Bool) : List Bool :=
  let q2_1 := x2
  let q3_1 := x3
  let q17_1 := x17
  let q19_1 := x19
  let q22_1 := x22
  let q23_1 := x23
  let q29_1 := x36
  let q30_1 := x30
  let q33_1 := x33
  let q33_2 := (Bool.xor q33_1 (c482 && q19_1))
  let q23_2 := (Bool.xor q23_1 (c482 && q19_1))
  let q33_3 := (Bool.xor q33_2 c482)
  let p_1 := (Bool.xor phase ((c482 && c481) && q17_1))
  let q19_2 := (Bool.xor q19_1 (c482 && (q23_2 && q33_3)))
  let q29_2 := (if c482 then q19_2 else q29_1)
  let q19_3 := (if c482 then q29_1 else q19_2)
  let p_2 := (Bool.xor p_1 ((c482 && c481) && q29_2))
  let p_3 := (Bool.xor p_2 (((c482 && c481) && q2_1) && q17_1))
  let p_4 := (Bool.xor p_3 (((c482 && c481) && q17_1) && q29_2))
  let p_5 := (Bool.xor p_4 (((c482 && c481) && q2_1) && q29_2))
  let q17_2 := (Bool.xor q17_1 (c482 && q29_2))
  let q29_3 := (Bool.xor q29_2 (c482 && q2_1))
  let q29_4 := (Bool.xor q29_3 c482)
  let q30_2 := (Bool.xor q30_1 (c482 && (q17_2 && q29_4)))
  let p_6 := (Bool.xor p_5 (c482 && q22_1))
  let q30_3 := (Bool.xor q30_2 (c482 && q29_4))
  let q30_4 := (Bool.xor q30_3 (c482 && q2_1))
  let q30_5 := (Bool.xor q30_4 c482)
  let p_7 := (Bool.xor p_6 (c482 && q30_5))
  let p_8 := (Bool.xor p_7 ((c482 && q3_1) && q22_1))
  let p_9 := (Bool.xor p_8 ((c482 && q22_1) && q30_5))
  let p_10 := (Bool.xor p_9 ((c482 && q3_1) && q30_5))
  let p_11 := (Bool.xor p_10 (c482 && (q30_5 && m0)))
  let q30_6 := (q30_5 && (Bool.not c482))
  let c483_1 := (if c482 then m0 else c483)
  let q29_5 := (Bool.xor q29_4 (c482 && q17_2))
  let q29_6 := (Bool.xor q29_5 (c482 && q2_1))
  let q29_7 := (Bool.xor q29_6 c482)
  let p_12 := (Bool.xor p_11 ((c482 && c483_1) && q29_7))
  let q29_8 := (Bool.xor q29_7 (c482 && q17_2))
  let p_13 := (Bool.xor p_12 ((c482 && c483_1) && q29_8))
  let q29_9 := (Bool.xor q29_8 (c482 && q17_2))
  let p_14 := (Bool.xor p_13 (((c482 && c483_1) && q2_1) && q29_9))
  let q17_3 := (Bool.xor q17_2 (c482 && q29_9))
  let p_15 := (Bool.xor p_14 (((c482 && c483_1) && q17_3) && q29_9))
  let p_16 := (Bool.xor p_15 (((c482 && c483_1) && q2_1) && q17_3))
  let q30_7 := (Bool.xor q30_6 (c482 && (q23_2 && q33_3)))
  let q30_8 := (Bool.xor q30_7 (c482 && q17_3))
  let q19_4 := (if c482 then q30_8 else q19_3)
  let q30_9 := (if c482 then q19_3 else q30_8)
  let p_17 := (Bool.xor p_16 (c482 && (q17_3 && m1)))
  let q17_4 := (q17_3 && (Bool.not c482))
  let c483_2 := (if c482 then m1 else c483_1)
  let q23_3 := (Bool.xor q23_2 (c482 && q19_4))
  let p_18 := (Bool.xor p_17 ((c482 && c483_2) && q23_3))
  let p_19 := (Bool.xor p_18 ((c482 && c483_2) && q19_4))
  let q33_4 := (Bool.xor q33_3 (c482 && q19_4))
  let q33_5 := (Bool.xor q33_4 c482)
  let p_20 := (Bool.xor p_19 (((c482 && c483_2) && q23_3) && q33_5))
  let p_21 := (Bool.xor p_20 (((c482 && c483_2) && q19_4) && q23_3))
  let p_22 := (Bool.xor p_21 (((c482 && c483_2) && q19_4) && q33_5))
  let q29_10 := (if c482 then q17_4 else q29_9)
  let q17_5 := (if c482 then q29_9 else q17_4)
  let q30_10 := (if c482 then q29_10 else q30_9)
  let q29_11 := (if c482 then q30_9 else q29_10)
  [q2_1, q3_1, q17_5, q19_4, q22_1, q23_3, false, q30_10, q33_5, q29_11, c481, c482, c483_2, p_22]

set_option maxHeartbeats 5000000 in
theorem actual_21910 (x2 x3 x17 x19 x22 x23 x30 x33 x36 c481 c482 c483 m0 m1 phase : Bool) :
    source21910 x2 x3 x17 x19 x22 x23 x30 x33 x36 c481 c482 c483 m0 m1 phase = candidate21910 x2 x3 x17 x19 x22 x23 x30 x33 x36 c481 c482 c483 m0 m1 phase := by
  cases c482 <;> simp [source21910, candidate21910] <;> first | rfl | bv_decide | decide +revert

def sourceGates21910 : List (List Nat) := [[129,482],[33,19,33],[33,19,23],[17,33],[49,23,33,29],[144,17,481],[33,19,29],[144,29,481],[160,2,17,481],[160,17,29,481],[160,2,29,481],[33,29,17],[33,2,29],[17,29],[49,17,29,30],[16,22],[33,29,30],[33,2,30],[17,30],[16,30],[32,3,22],[32,22,30],[32,3,30],[80,30,483],[33,17,29],[33,2,29],[17,29],[144,29,483],[33,17,29],[144,29,483],[33,17,29],[160,2,29,483],[33,29,17],[160,17,29,483],[160,2,17,483],[80,17,483],[33,19,23],[144,23,483],[144,19,483],[33,19,33],[17,33],[160,23,33,483],[160,19,23,483],[160,19,33,483],[34,29,17],[1]]
def candidateGates21910 : List (List Nat) := [[129,482],[33,19,33],[33,19,23],[17,33],[144,17,481],[49,23,33,19],[34,29,19],[144,29,481],[160,2,17,481],[160,17,29,481],[160,2,29,481],[33,29,17],[33,2,29],[17,29],[49,17,29,30],[16,22],[33,29,30],[33,2,30],[17,30],[16,30],[32,3,22],[32,22,30],[32,3,30],[80,30,483],[33,17,29],[33,2,29],[17,29],[144,29,483],[33,17,29],[144,29,483],[33,17,29],[160,2,29,483],[33,29,17],[160,17,29,483],[160,2,17,483],[49,23,33,30],[33,17,30],[34,19,30],[80,17,483],[33,19,23],[144,23,483],[144,19,483],[33,19,33],[17,33],[160,23,33,483],[160,19,23,483],[160,19,33,483],[34,29,17],[34,30,29],[1]]
theorem resource_21910 : countPaid sourceGates21910 = 2 ∧ countPaid candidateGates21910 = 3 ∧ within36 candidateGates21910 = true := by decide


-- Actual source operations [22561,22619); omitted entry and exit q23=0.
-- Both IF arms, all initial retained wires, all HMR outcomes, arbitrary phase.
def source22561 (x5 x10 x15 x18 x19 x24 x26 x32 x33 x35 x36 c479 c480 c483 m0 m1 m2 phase : Bool) : List Bool :=
  let q5_1 := x5
  let q10_1 := x10
  let q15_1 := x15
  let q18_1 := x18
  let q19_1 := x19
  let q23_1 := false
  let q24_1 := x24
  let q26_1 := x26
  let q32_1 := x32
  let q33_1 := x33
  let q35_1 := x35
  let q36_1 := x36
  let q23_2 := (Bool.xor q23_1 (c480 && (q5_1 && q18_1)))
  let p_1 := (Bool.xor phase ((c480 && c479) && q19_1))
  let q23_3 := (Bool.xor q23_2 (c480 && q18_1))
  let q23_4 := (Bool.xor q23_3 (c480 && q15_1))
  let p_2 := (Bool.xor p_1 ((c480 && c479) && q23_4))
  let q35_2 := (Bool.xor q35_1 (c480 && q19_1))
  let p_3 := (Bool.xor p_2 (((c480 && c479) && q19_1) && q35_2))
  let p_4 := (Bool.xor p_3 (((c480 && c479) && q19_1) && q23_4))
  let p_5 := (Bool.xor p_4 (((c480 && c479) && q23_4) && q35_2))
  let q35_3 := (Bool.xor q35_2 (c480 && q23_4))
  let q23_5 := (Bool.xor q23_4 (c480 && q19_1))
  let q35_4 := (Bool.xor q35_3 c480)
  let q26_2 := (Bool.xor q26_1 (c480 && (q23_5 && q35_4)))
  let q36_2 := (Bool.xor q36_1 (c480 && q26_2))
  let q26_3 := (Bool.xor q26_2 (c480 && q24_1))
  let q36_3 := (Bool.xor q36_2 (c480 && q23_5))
  let q26_4 := (Bool.xor q26_3 (c480 && q23_5))
  let q36_4 := (Bool.xor q36_3 (c480 && q19_1))
  let q26_5 := (Bool.xor q26_4 (c480 && q19_1))
  let q36_5 := (Bool.xor q36_4 c480)
  let q32_2 := (Bool.xor q32_1 (c480 && (q26_5 && q36_5)))
  let p_6 := (Bool.xor p_5 (c480 && q10_1))
  let q32_3 := (Bool.xor q32_2 (c480 && q26_5))
  let q32_4 := (Bool.xor q32_3 (c480 && q24_1))
  let p_7 := (Bool.xor p_6 (c480 && q32_4))
  let q33_2 := (Bool.xor q33_1 (c480 && q10_1))
  let p_8 := (Bool.xor p_7 ((c480 && q10_1) && q33_2))
  let p_9 := (Bool.xor p_8 ((c480 && q10_1) && q32_4))
  let p_10 := (Bool.xor p_9 ((c480 && q32_4) && q33_2))
  let p_11 := (Bool.xor p_10 (c480 && (q32_4 && m0)))
  let q32_5 := (q32_4 && (Bool.not c480))
  let c483_1 := (if c480 then m0 else c483)
  let p_12 := (Bool.xor p_11 ((c480 && c483_1) && q24_1))
  let q26_6 := (Bool.xor q26_5 (c480 && q24_1))
  let p_13 := (Bool.xor p_12 ((c480 && c483_1) && q26_6))
  let q36_6 := (Bool.xor q36_5 (c480 && q26_6))
  let q36_7 := (Bool.xor q36_6 c480)
  let p_14 := (Bool.xor p_13 (((c480 && c483_1) && q24_1) && q36_7))
  let p_15 := (Bool.xor p_14 (((c480 && c483_1) && q24_1) && q26_6))
  let p_16 := (Bool.xor p_15 (((c480 && c483_1) && q26_6) && q36_7))
  let p_17 := (Bool.xor p_16 (c480 && (q26_6 && m1)))
  let q26_7 := (q26_6 && (Bool.not c480))
  let c483_2 := (if c480 then m1 else c483_1)
  let p_18 := (Bool.xor p_17 ((c480 && c483_2) && q19_1))
  let q23_6 := (Bool.xor q23_5 (c480 && q19_1))
  let p_19 := (Bool.xor p_18 ((c480 && c483_2) && q23_6))
  let q35_5 := (Bool.xor q35_4 (c480 && q23_6))
  let q35_6 := (Bool.xor q35_5 c480)
  let p_20 := (Bool.xor p_19 (((c480 && c483_2) && q19_1) && q35_6))
  let p_21 := (Bool.xor p_20 (((c480 && c483_2) && q19_1) && q23_6))
  let p_22 := (Bool.xor p_21 (((c480 && c483_2) && q23_6) && q35_6))
  let p_23 := (Bool.xor p_22 (c480 && (q23_6 && m2)))
  let q23_7 := (q23_6 && (Bool.not c480))
  let c483_3 := (if c480 then m2 else c483_2)
  let p_24 := (Bool.xor p_23 ((c480 && c483_3) && q15_1))
  let p_25 := (Bool.xor p_24 ((c480 && c483_3) && q18_1))
  let p_26 := (Bool.xor p_25 (((c480 && c483_3) && q15_1) && q18_1))
  let q15_2 := (Bool.xor q15_1 (c480 && q5_1))
  let p_27 := (Bool.xor p_26 (((c480 && c483_3) && q15_2) && q18_1))
  let q35_7 := (Bool.xor q35_6 (c480 && q19_1))
  let q33_3 := (Bool.xor q33_2 (c480 && q10_1))
  let q15_3 := (Bool.xor q15_2 (c480 && q5_1))
  [q5_1, q10_1, q15_3, q18_1, q19_1, q23_7, q24_1, q26_7, q32_5, q33_3, q35_7, q36_7, c479, c480, c483_3, p_27]

def candidate22561 (x5 x10 x15 x18 x19 x24 x26 x32 x33 x35 x36 c479 c480 c483 m0 m1 m2 phase : Bool) : List Bool :=
  let q5_1 := x5
  let q10_1 := x10
  let q15_1 := x15
  let q18_1 := x18
  let q19_1 := x19
  let q23_1 := x36
  let q24_1 := x24
  let q26_1 := x26
  let q32_1 := x32
  let q33_1 := x33
  let q35_1 := x35
  let p_1 := (Bool.xor phase ((c480 && c479) && q19_1))
  let q15_2 := (Bool.xor q15_1 (c480 && (q5_1 && q18_1)))
  let q15_3 := (Bool.xor q15_2 (c480 && q18_1))
  let q23_2 := (if c480 then q15_3 else q23_1)
  let q15_4 := (if c480 then q23_1 else q15_3)
  let p_2 := (Bool.xor p_1 ((c480 && c479) && q23_2))
  let q35_2 := (Bool.xor q35_1 (c480 && q19_1))
  let p_3 := (Bool.xor p_2 (((c480 && c479) && q19_1) && q35_2))
  let p_4 := (Bool.xor p_3 (((c480 && c479) && q19_1) && q23_2))
  let p_5 := (Bool.xor p_4 (((c480 && c479) && q23_2) && q35_2))
  let q35_3 := (Bool.xor q35_2 (c480 && q23_2))
  let q23_3 := (Bool.xor q23_2 (c480 && q19_1))
  let q35_4 := (Bool.xor q35_3 c480)
  let q26_2 := (Bool.xor q26_1 (c480 && (q23_3 && q35_4)))
  let q15_5 := (Bool.xor q15_4 (c480 && q26_2))
  let q26_3 := (Bool.xor q26_2 (c480 && q24_1))
  let q15_6 := (Bool.xor q15_5 (c480 && q23_3))
  let q26_4 := (Bool.xor q26_3 (c480 && q23_3))
  let q15_7 := (Bool.xor q15_6 (c480 && q19_1))
  let q26_5 := (Bool.xor q26_4 (c480 && q19_1))
  let q15_8 := (Bool.xor q15_7 c480)
  let q32_2 := (Bool.xor q32_1 (c480 && (q26_5 && q15_8)))
  let p_6 := (Bool.xor p_5 (c480 && q10_1))
  let q32_3 := (Bool.xor q32_2 (c480 && q26_5))
  let q32_4 := (Bool.xor q32_3 (c480 && q24_1))
  let p_7 := (Bool.xor p_6 (c480 && q32_4))
  let q33_2 := (Bool.xor q33_1 (c480 && q10_1))
  let p_8 := (Bool.xor p_7 ((c480 && q10_1) && q33_2))
  let p_9 := (Bool.xor p_8 ((c480 && q10_1) && q32_4))
  let p_10 := (Bool.xor p_9 ((c480 && q32_4) && q33_2))
  let p_11 := (Bool.xor p_10 (c480 && (q32_4 && m0)))
  let q32_5 := (q32_4 && (Bool.not c480))
  let c483_1 := (if c480 then m0 else c483)
  let p_12 := (Bool.xor p_11 ((c480 && c483_1) && q24_1))
  let q26_6 := (Bool.xor q26_5 (c480 && q24_1))
  let p_13 := (Bool.xor p_12 ((c480 && c483_1) && q26_6))
  let q15_9 := (Bool.xor q15_8 (c480 && q26_6))
  let q15_10 := (Bool.xor q15_9 c480)
  let p_14 := (Bool.xor p_13 (((c480 && c483_1) && q24_1) && q15_10))
  let p_15 := (Bool.xor p_14 (((c480 && c483_1) && q24_1) && q26_6))
  let p_16 := (Bool.xor p_15 (((c480 && c483_1) && q26_6) && q15_10))
  let p_17 := (Bool.xor p_16 (c480 && (q26_6 && m1)))
  let q26_7 := (q26_6 && (Bool.not c480))
  let c483_2 := (if c480 then m1 else c483_1)
  let p_18 := (Bool.xor p_17 ((c480 && c483_2) && q19_1))
  let q23_4 := (Bool.xor q23_3 (c480 && q19_1))
  let p_19 := (Bool.xor p_18 ((c480 && c483_2) && q23_4))
  let q35_5 := (Bool.xor q35_4 (c480 && q23_4))
  let q35_6 := (Bool.xor q35_5 c480)
  let p_20 := (Bool.xor p_19 (((c480 && c483_2) && q19_1) && q35_6))
  let p_21 := (Bool.xor p_20 (((c480 && c483_2) && q19_1) && q23_4))
  let p_22 := (Bool.xor p_21 (((c480 && c483_2) && q23_4) && q35_6))
  let q26_8 := (Bool.xor q26_7 (c480 && (q5_1 && q18_1)))
  let q26_9 := (Bool.xor q26_8 (c480 && q18_1))
  let q26_10 := (Bool.xor q26_9 (c480 && q23_4))
  let q15_11 := (if c480 then q26_10 else q15_10)
  let q26_11 := (if c480 then q15_10 else q26_10)
  let p_23 := (Bool.xor p_22 (c480 && (q23_4 && m2)))
  let q23_5 := (q23_4 && (Bool.not c480))
  let c483_3 := (if c480 then m2 else c483_2)
  let p_24 := (Bool.xor p_23 ((c480 && c483_3) && q15_11))
  let p_25 := (Bool.xor p_24 ((c480 && c483_3) && q18_1))
  let p_26 := (Bool.xor p_25 (((c480 && c483_3) && q15_11) && q18_1))
  let q15_12 := (Bool.xor q15_11 (c480 && q5_1))
  let p_27 := (Bool.xor p_26 (((c480 && c483_3) && q15_12) && q18_1))
  let q35_7 := (Bool.xor q35_6 (c480 && q19_1))
  let q33_3 := (Bool.xor q33_2 (c480 && q10_1))
  let q15_13 := (Bool.xor q15_12 (c480 && q5_1))
  let q26_12 := (if c480 then q23_5 else q26_11)
  let q23_6 := (if c480 then q26_11 else q23_5)
  [q5_1, q10_1, q15_13, q18_1, q19_1, false, q24_1, q26_12, q32_5, q33_3, q35_7, q23_6, c479, c480, c483_3, p_27]

set_option maxHeartbeats 5000000 in
theorem actual_22561 (x5 x10 x15 x18 x19 x24 x26 x32 x33 x35 x36 c479 c480 c483 m0 m1 m2 phase : Bool) :
    source22561 x5 x10 x15 x18 x19 x24 x26 x32 x33 x35 x36 c479 c480 c483 m0 m1 m2 phase = candidate22561 x5 x10 x15 x18 x19 x24 x26 x32 x33 x35 x36 c479 c480 c483 m0 m1 m2 phase := by
  simp [source22561, candidate22561] <;> bv_decide

def sourceGates22561 : List (List Nat) := [[129,480],[49,5,18,23],[144,19,479],[33,18,23],[33,15,23],[144,23,479],[33,19,35],[160,19,35,479],[160,19,23,479],[160,23,35,479],[33,23,35],[33,19,23],[17,35],[49,23,35,26],[33,26,36],[33,24,26],[33,23,36],[33,23,26],[33,19,36],[33,19,26],[17,36],[49,26,36,32],[16,10],[33,26,32],[33,24,32],[16,32],[33,10,33],[32,10,33],[32,10,32],[32,32,33],[80,32,483],[144,24,483],[33,24,26],[144,26,483],[33,26,36],[17,36],[160,24,36,483],[160,24,26,483],[160,26,36,483],[80,26,483],[144,19,483],[33,19,23],[144,23,483],[33,23,35],[17,35],[160,19,35,483],[160,19,23,483],[160,23,35,483],[80,23,483],[144,15,483],[144,18,483],[160,15,18,483],[33,5,15],[160,15,18,483],[33,19,35],[33,10,33],[33,5,15],[1]]
def candidateGates22561 : List (List Nat) := [[129,480],[144,19,479],[49,5,18,15],[33,18,15],[34,23,15],[144,23,479],[33,19,35],[160,19,35,479],[160,19,23,479],[160,23,35,479],[33,23,35],[33,19,23],[17,35],[49,23,35,26],[33,26,15],[33,24,26],[33,23,15],[33,23,26],[33,19,15],[33,19,26],[17,15],[49,26,15,32],[16,10],[33,26,32],[33,24,32],[16,32],[33,10,33],[32,10,33],[32,10,32],[32,32,33],[80,32,483],[144,24,483],[33,24,26],[144,26,483],[33,26,15],[17,15],[160,24,15,483],[160,24,26,483],[160,26,15,483],[80,26,483],[144,19,483],[33,19,23],[144,23,483],[33,23,35],[17,35],[160,19,35,483],[160,19,23,483],[160,23,35,483],[49,5,18,26],[33,18,26],[33,23,26],[34,15,26],[80,23,483],[144,15,483],[144,18,483],[160,15,18,483],[33,5,15],[160,15,18,483],[33,19,35],[33,10,33],[33,5,15],[34,26,23],[1]]
theorem resource_22561 : countPaid sourceGates22561 = 3 ∧ countPaid candidateGates22561 = 4 ∧ within36 candidateGates22561 = true := by decide


-- Actual source operations [25804,25875); omitted entry and exit q10=0.
-- Both IF arms, all initial retained wires, all HMR outcomes, arbitrary phase.
def source25804 (x5 x7 x8 x15 x16 x19 x24 x25 x26 x29 x32 x36 c479 c480 c483 m0 m1 m2 phase : Bool) : List Bool :=
  let q5_1 := x5
  let q7_1 := x7
  let q8_1 := x8
  let q10_1 := false
  let q15_1 := x15
  let q16_1 := x16
  let q19_1 := x19
  let q24_1 := x24
  let q25_1 := x25
  let q26_1 := x26
  let q29_1 := x29
  let q32_1 := x32
  let q36_1 := x36
  let q8_2 := (Bool.xor q8_1 (c480 && q5_1))
  let q10_2 := (Bool.xor q10_1 (c480 && (q16_1 && q8_2)))
  let q36_2 := (Bool.xor q36_1 (c480 && q19_1))
  let p_1 := (Bool.xor phase ((c480 && c479) && q36_2))
  let q15_2 := (Bool.xor q15_1 (c480 && q10_2))
  let q15_3 := (Bool.xor q15_2 (c480 && q8_2))
  let p_2 := (Bool.xor p_1 ((c480 && c479) && q15_3))
  let p_3 := (Bool.xor p_2 (((c480 && c479) && q19_1) && q36_2))
  let p_4 := (Bool.xor p_3 (((c480 && c479) && q15_3) && q36_2))
  let p_5 := (Bool.xor p_4 (((c480 && c479) && q15_3) && q19_1))
  let q36_3 := (if c480 then q19_1 else q36_2)
  let q19_2 := (if c480 then q36_2 else q19_1)
  let q36_4 := (Bool.xor q36_3 (c480 && q15_3))
  let q19_3 := (Bool.xor q19_2 (c480 && q15_3))
  let q36_5 := (Bool.xor q36_4 c480)
  let q24_2 := (Bool.xor q24_1 (c480 && (q19_3 && q36_5)))
  let q32_2 := (Bool.xor q32_1 (c480 && q24_2))
  let q26_2 := (Bool.xor q26_1 (c480 && q24_2))
  let q32_3 := (Bool.xor q32_2 (c480 && q15_3))
  let q26_3 := (Bool.xor q26_2 (c480 && q15_3))
  let q32_4 := (Bool.xor q32_3 c480)
  let q29_2 := (Bool.xor q29_1 (c480 && (q26_3 && q32_4)))
  let p_6 := (Bool.xor p_5 (c480 && q25_1))
  let q29_3 := (Bool.xor q29_2 (c480 && q24_2))
  let q29_4 := (Bool.xor q29_3 (c480 && q15_3))
  let p_7 := (Bool.xor p_6 (c480 && q29_4))
  let p_8 := (Bool.xor p_7 ((c480 && q7_1) && q25_1))
  let p_9 := (Bool.xor p_8 ((c480 && q25_1) && q29_4))
  let p_10 := (Bool.xor p_9 ((c480 && q7_1) && q29_4))
  let p_11 := (Bool.xor p_10 (c480 && (q29_4 && m0)))
  let q29_5 := (q29_4 && (Bool.not c480))
  let c483_1 := (if c480 then m0 else c483)
  let q26_4 := (Bool.xor q26_3 (c480 && q24_2))
  let q26_5 := (Bool.xor q26_4 (c480 && q15_3))
  let p_12 := (Bool.xor p_11 ((c480 && c483_1) && q26_5))
  let q24_3 := (Bool.xor q24_2 (c480 && q15_3))
  let p_13 := (Bool.xor p_12 ((c480 && c483_1) && q24_3))
  let q32_5 := (Bool.xor q32_4 (c480 && q24_3))
  let q32_6 := (Bool.xor q32_5 c480)
  let p_14 := (Bool.xor p_13 (((c480 && c483_1) && q26_5) && q32_6))
  let p_15 := (Bool.xor p_14 (((c480 && c483_1) && q24_3) && q26_5))
  let p_16 := (Bool.xor p_15 (((c480 && c483_1) && q24_3) && q32_6))
  let p_17 := (Bool.xor p_16 (c480 && (q24_3 && m1)))
  let q24_4 := (q24_3 && (Bool.not c480))
  let c483_2 := (if c480 then m1 else c483_1)
  let q19_4 := (Bool.xor q19_3 (c480 && q15_3))
  let p_18 := (Bool.xor p_17 ((c480 && c483_2) && q19_4))
  let p_19 := (Bool.xor p_18 ((c480 && c483_2) && q15_3))
  let q36_6 := (Bool.xor q36_5 (c480 && q15_3))
  let q36_7 := (Bool.xor q36_6 c480)
  let p_20 := (Bool.xor p_19 (((c480 && c483_2) && q19_4) && q36_7))
  let p_21 := (Bool.xor p_20 (((c480 && c483_2) && q15_3) && q19_4))
  let p_22 := (Bool.xor p_21 (((c480 && c483_2) && q15_3) && q36_7))
  let q10_3 := (Bool.xor q10_2 (c480 && q16_1))
  let q10_4 := (Bool.xor q10_3 (c480 && q15_3))
  let q10_5 := (Bool.xor q10_4 (c480 && q5_1))
  let p_23 := (Bool.xor p_22 (c480 && (q15_3 && m2)))
  let q15_4 := (q15_3 && (Bool.not c480))
  let c483_3 := (if c480 then m2 else c483_2)
  let q16_2 := (Bool.xor q16_1 (c480 && q10_5))
  let q16_3 := (Bool.xor q16_2 (c480 && q8_2))
  let q16_4 := (Bool.xor q16_3 (c480 && q5_1))
  let p_24 := (Bool.xor p_23 ((c480 && c483_3) && q16_4))
  let p_25 := (Bool.xor p_24 ((c480 && c483_3) && q5_1))
  let p_26 := (Bool.xor p_25 (((c480 && c483_3) && q5_1) && q16_4))
  let q8_3 := (Bool.xor q8_2 (c480 && q5_1))
  let p_27 := (Bool.xor p_26 (((c480 && c483_3) && q8_3) && q16_4))
  let p_28 := (Bool.xor p_27 (((c480 && c483_3) && q5_1) && q8_3))
  let p_29 := (Bool.xor p_28 (((c480 && c483_3) && q5_1) && q10_5))
  let p_30 := (Bool.xor p_29 (((c480 && c483_3) && q8_3) && q10_5))
  let q10_6 := (if c480 then q15_4 else q10_5)
  let q15_5 := (if c480 then q10_5 else q15_4)
  let q19_5 := (Bool.xor q19_4 (c480 && q36_7))
  let q36_8 := (if c480 then q19_5 else q36_7)
  let q19_6 := (if c480 then q36_7 else q19_5)
  let q15_6 := (Bool.xor q15_5 (c480 && q16_4))
  let q16_5 := (if c480 then q15_6 else q16_4)
  let q15_7 := (if c480 then q16_4 else q15_6)
  let q16_6 := (Bool.xor q16_5 (c480 && q8_3))
  [q5_1, q7_1, q8_3, q10_6, q15_7, q16_6, q19_6, q24_4, q25_1, q26_5, q29_5, q32_6, q36_8, c479, c480, c483_3, p_30]

def candidate25804 (x5 x7 x8 x15 x16 x19 x24 x25 x26 x29 x32 x36 c479 c480 c483 m0 m1 m2 phase : Bool) : List Bool :=
  let q5_1 := x5
  let q7_1 := x7
  let q8_1 := x8
  let q10_1 := x36
  let q15_1 := x15
  let q16_1 := x16
  let q19_1 := x19
  let q24_1 := x24
  let q25_1 := x25
  let q26_1 := x26
  let q29_1 := x29
  let q32_1 := x32
  let q8_2 := (Bool.xor q8_1 (c480 && q5_1))
  let q10_2 := (Bool.xor q10_1 (c480 && q19_1))
  let p_1 := (Bool.xor phase ((c480 && c479) && q10_2))
  let q15_2 := (Bool.xor q15_1 (c480 && (q8_2 && q16_1)))
  let q15_3 := (Bool.xor q15_2 (c480 && q8_2))
  let p_2 := (Bool.xor p_1 ((c480 && c479) && q15_3))
  let p_3 := (Bool.xor p_2 (((c480 && c479) && q19_1) && q10_2))
  let p_4 := (Bool.xor p_3 (((c480 && c479) && q15_3) && q10_2))
  let p_5 := (Bool.xor p_4 (((c480 && c479) && q15_3) && q19_1))
  let q10_3 := (if c480 then q19_1 else q10_2)
  let q19_2 := (if c480 then q10_2 else q19_1)
  let q10_4 := (Bool.xor q10_3 (c480 && q15_3))
  let q19_3 := (Bool.xor q19_2 (c480 && q15_3))
  let q10_5 := (Bool.xor q10_4 c480)
  let q24_2 := (Bool.xor q24_1 (c480 && (q19_3 && q10_5)))
  let q32_2 := (Bool.xor q32_1 (c480 && q24_2))
  let q26_2 := (Bool.xor q26_1 (c480 && q24_2))
  let q32_3 := (Bool.xor q32_2 (c480 && q15_3))
  let q26_3 := (Bool.xor q26_2 (c480 && q15_3))
  let q32_4 := (Bool.xor q32_3 c480)
  let q29_2 := (Bool.xor q29_1 (c480 && (q26_3 && q32_4)))
  let p_6 := (Bool.xor p_5 (c480 && q25_1))
  let q29_3 := (Bool.xor q29_2 (c480 && q24_2))
  let q29_4 := (Bool.xor q29_3 (c480 && q15_3))
  let p_7 := (Bool.xor p_6 (c480 && q29_4))
  let p_8 := (Bool.xor p_7 ((c480 && q7_1) && q25_1))
  let p_9 := (Bool.xor p_8 ((c480 && q25_1) && q29_4))
  let p_10 := (Bool.xor p_9 ((c480 && q7_1) && q29_4))
  let p_11 := (Bool.xor p_10 (c480 && (q29_4 && m0)))
  let q29_5 := (q29_4 && (Bool.not c480))
  let c483_1 := (if c480 then m0 else c483)
  let q26_4 := (Bool.xor q26_3 (c480 && q24_2))
  let q26_5 := (Bool.xor q26_4 (c480 && q15_3))
  let p_12 := (Bool.xor p_11 ((c480 && c483_1) && q26_5))
  let q24_3 := (Bool.xor q24_2 (c480 && q15_3))
  let p_13 := (Bool.xor p_12 ((c480 && c483_1) && q24_3))
  let q32_5 := (Bool.xor q32_4 (c480 && q24_3))
  let q32_6 := (Bool.xor q32_5 c480)
  let p_14 := (Bool.xor p_13 (((c480 && c483_1) && q26_5) && q32_6))
  let p_15 := (Bool.xor p_14 (((c480 && c483_1) && q24_3) && q26_5))
  let p_16 := (Bool.xor p_15 (((c480 && c483_1) && q24_3) && q32_6))
  let p_17 := (Bool.xor p_16 (c480 && (q24_3 && m1)))
  let q24_4 := (q24_3 && (Bool.not c480))
  let c483_2 := (if c480 then m1 else c483_1)
  let q19_4 := (Bool.xor q19_3 (c480 && q15_3))
  let p_18 := (Bool.xor p_17 ((c480 && c483_2) && q19_4))
  let p_19 := (Bool.xor p_18 ((c480 && c483_2) && q15_3))
  let q10_6 := (Bool.xor q10_5 (c480 && q15_3))
  let q10_7 := (Bool.xor q10_6 c480)
  let p_20 := (Bool.xor p_19 (((c480 && c483_2) && q19_4) && q10_7))
  let p_21 := (Bool.xor p_20 (((c480 && c483_2) && q15_3) && q19_4))
  let p_22 := (Bool.xor p_21 (((c480 && c483_2) && q15_3) && q10_7))
  let q24_5 := (Bool.xor q24_4 (c480 && (q8_2 && q16_1)))
  let q24_6 := (Bool.xor q24_5 (c480 && q5_1))
  let q24_7 := (Bool.xor q24_6 (c480 && q15_3))
  let q24_8 := (Bool.xor q24_7 (c480 && q16_1))
  let q10_8 := (if c480 then q24_8 else q10_7)
  let q24_9 := (if c480 then q10_7 else q24_8)
  let p_23 := (Bool.xor p_22 (c480 && (q15_3 && m2)))
  let q15_4 := (q15_3 && (Bool.not c480))
  let c483_3 := (if c480 then m2 else c483_2)
  let q16_2 := (Bool.xor q16_1 (c480 && q10_8))
  let q16_3 := (Bool.xor q16_2 (c480 && q8_2))
  let q16_4 := (Bool.xor q16_3 (c480 && q5_1))
  let p_24 := (Bool.xor p_23 ((c480 && c483_3) && q16_4))
  let p_25 := (Bool.xor p_24 ((c480 && c483_3) && q5_1))
  let p_26 := (Bool.xor p_25 (((c480 && c483_3) && q5_1) && q16_4))
  let q8_3 := (Bool.xor q8_2 (c480 && q5_1))
  let p_27 := (Bool.xor p_26 (((c480 && c483_3) && q8_3) && q16_4))
  let p_28 := (Bool.xor p_27 (((c480 && c483_3) && q5_1) && q8_3))
  let p_29 := (Bool.xor p_28 (((c480 && c483_3) && q5_1) && q10_8))
  let p_30 := (Bool.xor p_29 (((c480 && c483_3) && q8_3) && q10_8))
  let q10_9 := (if c480 then q15_4 else q10_8)
  let q15_5 := (if c480 then q10_8 else q15_4)
  let q19_5 := (Bool.xor q19_4 (c480 && q24_9))
  let q24_10 := (if c480 then q19_5 else q24_9)
  let q19_6 := (if c480 then q24_9 else q19_5)
  let q15_6 := (Bool.xor q15_5 (c480 && q16_4))
  let q16_5 := (if c480 then q15_6 else q16_4)
  let q15_7 := (if c480 then q16_4 else q15_6)
  let q16_6 := (Bool.xor q16_5 (c480 && q8_3))
  let q24_11 := (if c480 then q10_9 else q24_10)
  let q10_10 := (if c480 then q24_10 else q10_9)
  [q5_1, q7_1, q8_3, false, q15_7, q16_6, q19_6, q24_11, q25_1, q26_5, q29_5, q32_6, q10_10, c479, c480, c483_3, p_30]

set_option maxHeartbeats 5000000 in
theorem actual_25804 (x5 x7 x8 x15 x16 x19 x24 x25 x26 x29 x32 x36 c479 c480 c483 m0 m1 m2 phase : Bool) :
    source25804 x5 x7 x8 x15 x16 x19 x24 x25 x26 x29 x32 x36 c479 c480 c483 m0 m1 m2 phase = candidate25804 x5 x7 x8 x15 x16 x19 x24 x25 x26 x29 x32 x36 c479 c480 c483 m0 m1 m2 phase := by
  cases c480 <;> simp [source25804, candidate25804] <;> first | rfl | bv_decide | decide +revert

def sourceGates25804 : List (List Nat) := [[129,480],[33,5,8],[49,16,8,10],[33,19,36],[144,36,479],[33,10,15],[33,8,15],[144,15,479],[160,19,36,479],[160,15,36,479],[160,15,19,479],[34,36,19],[33,15,36],[33,15,19],[17,36],[49,19,36,24],[33,24,32],[33,24,26],[33,15,32],[33,15,26],[17,32],[49,26,32,29],[16,25],[33,24,29],[33,15,29],[16,29],[32,7,25],[32,25,29],[32,7,29],[80,29,483],[33,24,26],[33,15,26],[144,26,483],[33,15,24],[144,24,483],[33,24,32],[17,32],[160,26,32,483],[160,24,26,483],[160,24,32,483],[80,24,483],[33,15,19],[144,19,483],[144,15,483],[33,15,36],[17,36],[160,19,36,483],[160,15,19,483],[160,15,36,483],[33,16,10],[33,15,10],[33,5,10],[80,15,483],[33,10,16],[33,8,16],[33,5,16],[144,16,483],[144,5,483],[160,5,16,483],[33,5,8],[160,8,16,483],[160,5,8,483],[160,5,10,483],[160,8,10,483],[34,10,15],[33,36,19],[34,36,19],[33,16,15],[34,16,15],[33,8,16],[1]]
def candidateGates25804 : List (List Nat) := [[129,480],[33,5,8],[33,19,10],[144,10,479],[49,8,16,15],[33,8,15],[144,15,479],[160,19,10,479],[160,15,10,479],[160,15,19,479],[34,10,19],[33,15,10],[33,15,19],[17,10],[49,19,10,24],[33,24,32],[33,24,26],[33,15,32],[33,15,26],[17,32],[49,26,32,29],[16,25],[33,24,29],[33,15,29],[16,29],[32,7,25],[32,25,29],[32,7,29],[80,29,483],[33,24,26],[33,15,26],[144,26,483],[33,15,24],[144,24,483],[33,24,32],[17,32],[160,26,32,483],[160,24,26,483],[160,24,32,483],[80,24,483],[33,15,19],[144,19,483],[144,15,483],[33,15,10],[17,10],[160,19,10,483],[160,15,19,483],[160,15,10,483],[49,8,16,24],[33,5,24],[33,15,24],[33,16,24],[34,10,24],[80,15,483],[33,10,16],[33,8,16],[33,5,16],[144,16,483],[144,5,483],[160,5,16,483],[33,5,8],[160,8,16,483],[160,5,8,483],[160,5,10,483],[160,8,10,483],[34,10,15],[33,24,19],[34,24,19],[33,16,15],[34,16,15],[33,8,16],[34,24,10],[1]]
theorem resource_25804 : countPaid sourceGates25804 = 3 ∧ countPaid candidateGates25804 = 4 ∧ within36 candidateGates25804 = true := by decide

end GVQCCV6
