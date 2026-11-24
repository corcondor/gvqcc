import Std.Tactic.BVDecide

/-! V10: measured sink transposition.
Full-span gate lists encode the actual V9 native ranges. For every initial
Boolean coordinate, classical input, active guard and HMR result, each
transformed span has the same final Boolean coordinates, sign and classical
state. The BDD verifier independently checks complete serialized KMB.
The virtual accumulator lemma assumes q36 starts at zero and the omitted
measurement outcome has no effect at the complete gap boundary (BDD proof).
No full quantum-channel or score theorem is claimed. -/
namespace GVQCCV10

def bx := Bool.xor

theorem measurement_sink (g t a b m p : Bool) :
  bx p (g && m && bx t (g && a && b)) =
  bx (bx p (g && m && t)) (g && m && a && b) := by
  cases g <;> cases t <;> cases a <;> cases b <;> cases m <;> cases p <;> decide

def parity : List Bool → Bool
  | [] => false
  | x :: xs => bx x (parity xs)

theorem parity_measure (m : Bool) (xs : List Bool) :
    (m && parity xs) = parity (xs.map (fun x => m && x)) := by
  induction xs with
  | nil => cases m <;> rfl
  | cons x xs ih =>
    simp only [parity, List.map]
    rw [← ih]
    cases m <;> cases x <;> cases parity xs <;> decide

theorem virtual_accumulator (a b c u v : Bool) :
  let f := bx (bx (a && b) a) c
  let h := bx true (bx u v)
  (f && h) = bx (bx (a && b && h) (a && h)) (c && h) := by
  cases a <;> cases b <;> cases c <;> cases u <;> cases v <;> decide

-- V9 native [174,227), HMR 78869, target 22.
def old174 (x0 x1 x3 x5 x7 x9 x11 x13 x15 x17 x19 x20 x21 x22 x23 x24 x25 x26 x27 x28 x29 x32 x33 x34 x35 c78869 active phase m : Bool) : List Bool :=
  let q0 := (Bool.xor x22 ((active && x21) && x0))
  let q1 := (Bool.xor x0 active)
  let q2 := (Bool.xor x1 active)
  let q3 := (Bool.xor q1 (active && x20))
  let q4 := (Bool.xor x34 ((active && x21) && q2))
  let q5 := (Bool.xor q2 (active && x5))
  let q6 := (Bool.xor x23 active)
  let q7 := (Bool.xor x32 ((active && q6) && q5))
  let q8 := (Bool.xor q6 active)
  let q9 := (Bool.xor x21 (active && q8))
  let q10 := (Bool.xor q9 (active && x24))
  let q11 := (Bool.xor x33 ((active && q10) && x7))
  let q12 := (Bool.xor q10 active)
  let q13 := (Bool.xor q12 (active && x24))
  let q14 := (Bool.xor x3 (active && x5))
  let q15 := (Bool.xor q14 (active && x9))
  let q16 := (Bool.xor q15 (active && x11))
  let q17 := (Bool.xor q16 (active && x15))
  let q18 := (Bool.xor q17 (active && x17))
  let q19 := (Bool.xor q13 (active && x25))
  let q20 := (Bool.xor q19 (active && x26))
  let q21 := (Bool.xor q20 (active && x28))
  let q22 := (Bool.xor q21 (active && x29))
  let q23 := (Bool.xor x35 ((active && q22) && q18))
  let q24 := (Bool.xor q5 (active && x13))
  let q25 := (Bool.xor q18 (active && x13))
  let q26 := (Bool.xor x13 (active && q24))
  let q27 := (Bool.xor x15 (active && q25))
  let q28 := (Bool.xor q24 (active && x7))
  let q29 := (Bool.xor q25 (active && x7))
  let q30 := (Bool.xor x7 (active && q11))
  let q31 := (Bool.xor q22 (active && x27))
  let q32 := (Bool.xor q31 (active && x24))
  let q33 := (Bool.xor q26 (active && x5))
  let q34 := (Bool.xor q30 (active && q4))
  let q35 := (Bool.xor q27 (active && x9))
  let q36 := (Bool.xor q28 (active && x11))
  let q37 := (Bool.xor q36 (active && x17))
  let q38 := (Bool.xor q35 (active && x17))
  let q39 := (Bool.xor q34 (active && x17))
  let q40 := (Bool.xor q37 (active && x19))
  let q41 := (Bool.xor q29 (active && q33))
  let q42 := (Bool.xor q39 (active && q40))
  let q43 := (Bool.xor q42 (active && q38))
  let q44 := (Bool.xor q33 ((active && q32) && q38))
  let q45 := (Bool.xor q32 (active && x29))
  let q46 := (Bool.xor q45 (active && x28))
  let q47 := (Bool.xor q46 (active && x27))
  let q48 := (Bool.xor q47 (active && x26))
  let q49 := (Bool.xor q48 (active && x25))
  let q50 := (Bool.xor q49 (active && x24))
  let q51 := (Bool.xor q50 (active && q8))
  let p52 := (Bool.xor phase ((active && 78869) && q0))
  let q53 := (q0 && (!active))
  let c54 := (if active then m else c78869)
  [q3, q40, q41, x5, q43, x9, x11, q44, q38, x17, x19, x20, q51, q53, q8, x24, x25, x26, x27, x28, x29, q7, q11, q4, q23, c54, p52]
def new174 (x0 x1 x3 x5 x7 x9 x11 x13 x15 x17 x19 x20 x21 x22 x23 x24 x25 x26 x27 x28 x29 x32 x33 x34 x35 c78869 active phase m : Bool) : List Bool :=
  let p0 := (Bool.xor phase ((active && 78869) && x22))
  let q1 := (x22 && (!active))
  let c2 := (if active then m else c78869)
  let p3 := (Bool.xor p0 (((active && c2) && x21) && x0))
  let q4 := (Bool.xor x0 active)
  let q5 := (Bool.xor x1 active)
  let q6 := (Bool.xor q4 (active && x20))
  let q7 := (Bool.xor x34 ((active && x21) && q5))
  let q8 := (Bool.xor q5 (active && x5))
  let q9 := (Bool.xor x23 active)
  let q10 := (Bool.xor x32 ((active && q9) && q8))
  let q11 := (Bool.xor q9 active)
  let q12 := (Bool.xor x21 (active && q11))
  let q13 := (Bool.xor q12 (active && x24))
  let q14 := (Bool.xor x33 ((active && q13) && x7))
  let q15 := (Bool.xor q13 active)
  let q16 := (Bool.xor q15 (active && x24))
  let q17 := (Bool.xor x3 (active && x5))
  let q18 := (Bool.xor q17 (active && x9))
  let q19 := (Bool.xor q18 (active && x11))
  let q20 := (Bool.xor q19 (active && x15))
  let q21 := (Bool.xor q20 (active && x17))
  let q22 := (Bool.xor q16 (active && x25))
  let q23 := (Bool.xor q22 (active && x26))
  let q24 := (Bool.xor q23 (active && x28))
  let q25 := (Bool.xor q24 (active && x29))
  let q26 := (Bool.xor x35 ((active && q25) && q21))
  let q27 := (Bool.xor q8 (active && x13))
  let q28 := (Bool.xor q21 (active && x13))
  let q29 := (Bool.xor x13 (active && q27))
  let q30 := (Bool.xor x15 (active && q28))
  let q31 := (Bool.xor q27 (active && x7))
  let q32 := (Bool.xor q28 (active && x7))
  let q33 := (Bool.xor x7 (active && q14))
  let q34 := (Bool.xor q25 (active && x27))
  let q35 := (Bool.xor q34 (active && x24))
  let q36 := (Bool.xor q29 (active && x5))
  let q37 := (Bool.xor q33 (active && q7))
  let q38 := (Bool.xor q30 (active && x9))
  let q39 := (Bool.xor q31 (active && x11))
  let q40 := (Bool.xor q39 (active && x17))
  let q41 := (Bool.xor q38 (active && x17))
  let q42 := (Bool.xor q37 (active && x17))
  let q43 := (Bool.xor q40 (active && x19))
  let q44 := (Bool.xor q32 (active && q36))
  let q45 := (Bool.xor q42 (active && q43))
  let q46 := (Bool.xor q45 (active && q41))
  let q47 := (Bool.xor q36 ((active && q35) && q41))
  let q48 := (Bool.xor q35 (active && x29))
  let q49 := (Bool.xor q48 (active && x28))
  let q50 := (Bool.xor q49 (active && x27))
  let q51 := (Bool.xor q50 (active && x26))
  let q52 := (Bool.xor q51 (active && x25))
  let q53 := (Bool.xor q52 (active && x24))
  let q54 := (Bool.xor q53 (active && q11))
  [q6, q43, q44, x5, q46, x9, x11, q47, q41, x17, x19, x20, q54, q1, q11, x24, x25, x26, x27, x28, x29, q10, q14, q7, q26, c2, p3]

set_option maxHeartbeats 6000000 in
theorem actual_174_227 (x0 x1 x3 x5 x7 x9 x11 x13 x15 x17 x19 x20 x21 x22 x23 x24 x25 x26 x27 x28 x29 x32 x33 x34 x35 c78869 active phase m : Bool) :
    old174 x0 x1 x3 x5 x7 x9 x11 x13 x15 x17 x19 x20 x21 x22 x23 x24 x25 x26 x27 x28 x29 x32 x33 x34 x35 c78869 active phase m = new174 x0 x1 x3 x5 x7 x9 x11 x13 x15 x17 x19 x20 x21 x22 x23 x24 x25 x26 x27 x28 x29 x32 x33 x34 x35 c78869 active phase m := by
  simp only [old174, new174]
  bv_decide

-- V9 native [6142,6159), HMR 531, target 33.
def old6142 (x0 x8 x15 x23 x33 x34 c530 c531 active phase m : Bool) : List Bool :=
  let q0 := (Bool.xor x33 ((active && x0) && x8))
  let q1 := (Bool.xor x34 active)
  let q2 := (Bool.xor x0 active)
  let q3 := (Bool.xor q0 (active && q2))
  let q4 := (Bool.xor q3 (active && x8))
  let q5 := (Bool.xor x23 (active && x8))
  let q6 := (Bool.xor q2 (active && x15))
  let q7 := (Bool.xor q1 (active && q6))
  let q8 := (Bool.xor q5 (active && q7))
  let g9 := (active && c530)
  let p10 := (Bool.xor phase ((g9 && q6) && q8))
  let q11 := (Bool.xor q8 (active && x8))
  let q12 := (Bool.xor q11 (active && q7))
  let q13 := (Bool.xor q6 active)
  let q14 := (Bool.xor q13 (active && q7))
  let p15 := (Bool.xor p10 ((active && 531) && q4))
  let q16 := (q4 && (!active))
  let c17 := (if active then m else c531)
  [q14, x8, x15, q12, q16, q7, c530, c17, p15]
def new6142 (x0 x8 x15 x23 x33 x34 c530 c531 active phase m : Bool) : List Bool :=
  let p0 := (Bool.xor phase ((active && 531) && x33))
  let q1 := (x33 && (!active))
  let c2 := (if active then m else c531)
  let p3 := (Bool.xor p0 (((active && c2) && x0) && x8))
  let q4 := (Bool.xor x34 active)
  let q5 := (Bool.xor x0 active)
  let p6 := (Bool.xor p3 ((active && c2) && q5))
  let p7 := (Bool.xor p6 ((active && c2) && x8))
  let q8 := (Bool.xor x23 (active && x8))
  let q9 := (Bool.xor q5 (active && x15))
  let q10 := (Bool.xor q4 (active && q9))
  let q11 := (Bool.xor q8 (active && q10))
  let g12 := (active && c530)
  let p13 := (Bool.xor p7 ((g12 && q9) && q11))
  let q14 := (Bool.xor q11 (active && x8))
  let q15 := (Bool.xor q14 (active && q10))
  let q16 := (Bool.xor q9 active)
  let q17 := (Bool.xor q16 (active && q10))
  [q17, x8, x15, q15, q1, q10, c530, c2, p13]

set_option maxHeartbeats 6000000 in
theorem actual_6142_6159 (x0 x8 x15 x23 x33 x34 c530 c531 active phase m : Bool) :
    old6142 x0 x8 x15 x23 x33 x34 c530 c531 active phase m = new6142 x0 x8 x15 x23 x33 x34 c530 c531 active phase m := by
  simp only [old6142, new6142]
  bv_decide

-- V9 native [6177,6200), HMR 539, target 33.
def old6177 (x4 x5 x7 x10 x11 x12 x14 x16 x17 x23 x24 x32 x33 x35 c539 active phase m : Bool) : List Bool :=
  let q0 := (Bool.xor x33 ((active && x10) && x24))
  let q1 := (Bool.xor x24 (active && x17))
  let q2 := (Bool.xor x10 (active && x7))
  let q3 := (Bool.xor q2 (active && x17))
  let q4 := (Bool.xor x16 active)
  let q5 := (Bool.xor q4 (active && x7))
  let q6 := (Bool.xor x12 active)
  let q7 := (Bool.xor q6 (active && x7))
  let q8 := (Bool.xor x11 active)
  let q9 := (Bool.xor q8 (active && x7))
  let q10 := (Bool.xor x5 active)
  let q11 := (Bool.xor q10 (active && x7))
  let q12 := (Bool.xor x35 active)
  let q13 := (Bool.xor q12 (active && x7))
  let q14 := (Bool.xor x4 active)
  let q15 := (Bool.xor q14 (active && x7))
  let q16 := (Bool.xor x32 active)
  let q17 := (Bool.xor q16 (active && x7))
  let q18 := (Bool.xor x14 active)
  let q19 := (Bool.xor q18 (active && x7))
  let q20 := (Bool.xor x23 active)
  let q21 := (Bool.xor q20 (active && x7))
  let p22 := (Bool.xor phase ((active && 539) && q0))
  let q23 := (q0 && (!active))
  let c24 := (if active then m else c539)
  [q15, q11, x7, q3, q9, q7, q19, q5, x17, q21, q1, q17, q23, q13, c24, p22]
def new6177 (x4 x5 x7 x10 x11 x12 x14 x16 x17 x23 x24 x32 x33 x35 c539 active phase m : Bool) : List Bool :=
  let p0 := (Bool.xor phase ((active && 539) && x33))
  let q1 := (x33 && (!active))
  let c2 := (if active then m else c539)
  let p3 := (Bool.xor p0 (((active && c2) && x10) && x24))
  let q4 := (Bool.xor x24 (active && x17))
  let q5 := (Bool.xor x10 (active && x7))
  let q6 := (Bool.xor q5 (active && x17))
  let q7 := (Bool.xor x16 active)
  let q8 := (Bool.xor q7 (active && x7))
  let q9 := (Bool.xor x12 active)
  let q10 := (Bool.xor q9 (active && x7))
  let q11 := (Bool.xor x11 active)
  let q12 := (Bool.xor q11 (active && x7))
  let q13 := (Bool.xor x5 active)
  let q14 := (Bool.xor q13 (active && x7))
  let q15 := (Bool.xor x35 active)
  let q16 := (Bool.xor q15 (active && x7))
  let q17 := (Bool.xor x4 active)
  let q18 := (Bool.xor q17 (active && x7))
  let q19 := (Bool.xor x32 active)
  let q20 := (Bool.xor q19 (active && x7))
  let q21 := (Bool.xor x14 active)
  let q22 := (Bool.xor q21 (active && x7))
  let q23 := (Bool.xor x23 active)
  let q24 := (Bool.xor q23 (active && x7))
  [q18, q14, x7, q6, q12, q10, q22, q8, x17, q24, q4, q20, q1, q16, c2, p3]

set_option maxHeartbeats 6000000 in
theorem actual_6177_6200 (x4 x5 x7 x10 x11 x12 x14 x16 x17 x23 x24 x32 x33 x35 c539 active phase m : Bool) :
    old6177 x4 x5 x7 x10 x11 x12 x14 x16 x17 x23 x24 x32 x33 x35 c539 active phase m = new6177 x4 x5 x7 x10 x11 x12 x14 x16 x17 x23 x24 x32 x33 x35 c539 active phase m := by
  simp only [old6177, new6177]
  bv_decide

-- V9 native [20449,20460), HMR 795, target 2.
def old20449 (x2 x8 x10 x14 x27 x28 x33 c795 active phase m : Bool) : List Bool :=
  let q0 := (Bool.xor x2 ((active && x10) && x8))
  let q1 := (Bool.xor x10 (active && x33))
  let q2 := (Bool.xor x14 (active && x28))
  let q3 := (Bool.xor q1 (active && x28))
  let q4 := (Bool.xor q3 (active && x27))
  let q5 := (Bool.xor x8 (active && q2))
  let q6 := (Bool.xor q0 ((active && q2) && x27))
  let q7 := (Bool.xor q6 (active && q5))
  let q8 := (Bool.xor q7 (active && q2))
  let q9 := (Bool.xor q2 (active && x28))
  let p10 := (Bool.xor phase ((active && 795) && q8))
  let q11 := (q8 && (!active))
  let c12 := (if active then m else c795)
  [q11, q5, q4, q9, x27, x28, x33, c12, p10]
def new20449 (x2 x8 x10 x14 x27 x28 x33 c795 active phase m : Bool) : List Bool :=
  let p0 := (Bool.xor phase ((active && 795) && x2))
  let q1 := (x2 && (!active))
  let c2 := (if active then m else c795)
  let p3 := (Bool.xor p0 (((active && c2) && x10) && x8))
  let q4 := (Bool.xor x10 (active && x33))
  let q5 := (Bool.xor x14 (active && x28))
  let q6 := (Bool.xor q4 (active && x28))
  let q7 := (Bool.xor q6 (active && x27))
  let q8 := (Bool.xor x8 (active && q5))
  let p9 := (Bool.xor p3 (((active && c2) && q5) && x27))
  let p10 := (Bool.xor p9 ((active && c2) && q8))
  let p11 := (Bool.xor p10 ((active && c2) && q5))
  let q12 := (Bool.xor q5 (active && x28))
  [q1, q8, q7, q12, x27, x28, x33, c2, p11]

set_option maxHeartbeats 6000000 in
theorem actual_20449_20460 (x2 x8 x10 x14 x27 x28 x33 c795 active phase m : Bool) :
    old20449 x2 x8 x10 x14 x27 x28 x33 c795 active phase m = new20449 x2 x8 x10 x14 x27 x28 x33 c795 active phase m := by
  simp only [old20449, new20449]
  bv_decide

-- V9 native [22476,22553), HMR 78893, target 7.
def old22476 (x0 x3 x4 x5 x6 x7 x11 x12 x13 x15 x17 x19 x23 x25 x30 x33 x34 c257 c258 c259 c419 c9801 c78893 active phase m : Bool) : List Bool :=
  let q0 := (Bool.xor x7 ((active && x5) && x23))
  let q1 := (Bool.xor x19 (active && x3))
  let q2 := (Bool.xor x5 (active && x12))
  let q3 := (Bool.xor x3 (active && q1))
  let q4 := (Bool.xor x12 (active && q1))
  let q5 := (Bool.xor x6 (active && q1))
  let q6 := (Bool.xor q2 (active && q1))
  let q7 := (Bool.xor q1 (active && q5))
  let q8 := (Bool.xor x17 (active && q5))
  let q9 := (Bool.xor q5 (active && q8))
  let q10 := (Bool.xor x34 (active && q8))
  let q11 := (Bool.xor q8 (active && q10))
  let q12 := (Bool.xor x30 (active && q10))
  let q13 := (Bool.xor q10 (active && q12))
  let q14 := (Bool.xor q4 (active && q6))
  let q15 := (Bool.xor q12 (active && q6))
  let q16 := (Bool.xor x33 ((active && q6) && q15))
  let c17 := (if active then false else c9801)
  let c18 := (if active then (!c17) else c17)
  let c19 := (if (active && c419) then (!c18) else c18)
  let q20 := (Bool.xor x11 ((active && c19) && q16))
  let g21 := (active && c257)
  let p22 := (Bool.xor phase (g21 && q6))
  let p23 := (Bool.xor p22 (g21 && q15))
  let p24 := (Bool.xor p23 (g21 && q3))
  let p25 := (Bool.xor p24 (g21 && q16))
  let g26 := (active && c419)
  let q27 := (Bool.xor q16 (active && q3))
  let q28 := (Bool.xor q15 (active && q27))
  let q29 := (Bool.xor q27 (active && q28))
  let q30 := (Bool.xor q6 (active && q28))
  let q31 := (Bool.xor q28 (active && q30))
  let q32 := (Bool.xor x4 (active && q30))
  let q33 := (Bool.xor q30 (active && q13))
  let q34 := (Bool.xor q33 (active && q9))
  let q35 := (Bool.xor q34 (active && q14))
  let q36 := (Bool.xor q35 (active && q11))
  let q37 := (Bool.xor x0 ((active && q36) && q32))
  let g38 := (active && c258)
  let p39 := (Bool.xor p25 (g38 && q36))
  let p40 := (Bool.xor p39 (g38 && q14))
  let p41 := (Bool.xor p40 (g38 && q13))
  let p42 := (Bool.xor p41 (g38 && q11))
  let p43 := (Bool.xor p42 (g38 && q9))
  let p44 := (Bool.xor p43 (g38 && q37))
  let q45 := (Bool.xor q37 (active && q11))
  let q46 := (Bool.xor q45 (active && q36))
  let q47 := (Bool.xor x15 (active && q14))
  let q48 := (Bool.xor q47 (active && q46))
  let q49 := (Bool.xor q46 (active && q3))
  let q50 := (Bool.xor q48 (active && q9))
  let q51 := (Bool.xor q49 (active && q29))
  let q52 := (Bool.xor q50 (active && q13))
  let q53 := (Bool.xor q51 (active && q31))
  let q54 := (Bool.xor x25 ((active && q53) && q52))
  let g55 := (active && c259)
  let p56 := (Bool.xor p44 (g55 && q53))
  let p57 := (Bool.xor p56 (g55 && q31))
  let p58 := (Bool.xor p57 (g55 && q29))
  let p59 := (Bool.xor p58 (g55 && q14))
  let p60 := (Bool.xor p59 (g55 && q13))
  let p61 := (Bool.xor p60 (g55 && q9))
  let p62 := (Bool.xor p61 (g55 && q3))
  let p63 := (Bool.xor p62 (g55 && q54))
  let q64 := (Bool.xor q54 (active && x23))
  let q65 := (Bool.xor x13 (active && x23))
  let q66 := (Bool.xor q14 (active && q65))
  let q67 := (Bool.xor q64 (active && q13))
  let q68 := (Bool.xor q67 (active && q3))
  let q69 := (Bool.xor q65 (active && q66))
  let q70 := (Bool.xor q68 (active && q9))
  let q71 := (Bool.xor q29 (active && q70))
  let p72 := (Bool.xor p63 ((active && 78893) && q0))
  let q73 := (q0 && (!active))
  let c74 := (if active then m else c78893)
  [q53, q3, q32, q36, q9, q73, q20, q66, q69, q52, q11, q7, x23, q70, q31, q71, q13, c257, c258, c259, c419, c19, c74, p72]
def new22476 (x0 x3 x4 x5 x6 x7 x11 x12 x13 x15 x17 x19 x23 x25 x30 x33 x34 c257 c258 c259 c419 c9801 c78893 active phase m : Bool) : List Bool :=
  let p0 := (Bool.xor phase ((active && 78893) && x7))
  let q1 := (x7 && (!active))
  let c2 := (if active then m else c78893)
  let p3 := (Bool.xor p0 (((active && c2) && x5) && x23))
  let q4 := (Bool.xor x19 (active && x3))
  let q5 := (Bool.xor x5 (active && x12))
  let q6 := (Bool.xor x3 (active && q4))
  let q7 := (Bool.xor x12 (active && q4))
  let q8 := (Bool.xor x6 (active && q4))
  let q9 := (Bool.xor q5 (active && q4))
  let q10 := (Bool.xor q4 (active && q8))
  let q11 := (Bool.xor x17 (active && q8))
  let q12 := (Bool.xor q8 (active && q11))
  let q13 := (Bool.xor x34 (active && q11))
  let q14 := (Bool.xor q11 (active && q13))
  let q15 := (Bool.xor x30 (active && q13))
  let q16 := (Bool.xor q13 (active && q15))
  let q17 := (Bool.xor q7 (active && q9))
  let q18 := (Bool.xor q15 (active && q9))
  let q19 := (Bool.xor x33 ((active && q9) && q18))
  let c20 := (if active then false else c9801)
  let c21 := (if active then (!c20) else c20)
  let c22 := (if (active && c419) then (!c21) else c21)
  let q23 := (Bool.xor x11 ((active && c22) && q19))
  let g24 := (active && c257)
  let p25 := (Bool.xor p3 (g24 && q9))
  let p26 := (Bool.xor p25 (g24 && q18))
  let p27 := (Bool.xor p26 (g24 && q6))
  let p28 := (Bool.xor p27 (g24 && q19))
  let g29 := (active && c419)
  let q30 := (Bool.xor q19 (active && q6))
  let q31 := (Bool.xor q18 (active && q30))
  let q32 := (Bool.xor q30 (active && q31))
  let q33 := (Bool.xor q9 (active && q31))
  let q34 := (Bool.xor q31 (active && q33))
  let q35 := (Bool.xor x4 (active && q33))
  let q36 := (Bool.xor q33 (active && q16))
  let q37 := (Bool.xor q36 (active && q12))
  let q38 := (Bool.xor q37 (active && q17))
  let q39 := (Bool.xor q38 (active && q14))
  let q40 := (Bool.xor x0 ((active && q39) && q35))
  let g41 := (active && c258)
  let p42 := (Bool.xor p28 (g41 && q39))
  let p43 := (Bool.xor p42 (g41 && q17))
  let p44 := (Bool.xor p43 (g41 && q16))
  let p45 := (Bool.xor p44 (g41 && q14))
  let p46 := (Bool.xor p45 (g41 && q12))
  let p47 := (Bool.xor p46 (g41 && q40))
  let q48 := (Bool.xor q40 (active && q14))
  let q49 := (Bool.xor q48 (active && q39))
  let q50 := (Bool.xor x15 (active && q17))
  let q51 := (Bool.xor q50 (active && q49))
  let q52 := (Bool.xor q49 (active && q6))
  let q53 := (Bool.xor q51 (active && q12))
  let q54 := (Bool.xor q52 (active && q32))
  let q55 := (Bool.xor q53 (active && q16))
  let q56 := (Bool.xor q54 (active && q34))
  let q57 := (Bool.xor x25 ((active && q56) && q55))
  let g58 := (active && c259)
  let p59 := (Bool.xor p47 (g58 && q56))
  let p60 := (Bool.xor p59 (g58 && q34))
  let p61 := (Bool.xor p60 (g58 && q32))
  let p62 := (Bool.xor p61 (g58 && q17))
  let p63 := (Bool.xor p62 (g58 && q16))
  let p64 := (Bool.xor p63 (g58 && q12))
  let p65 := (Bool.xor p64 (g58 && q6))
  let p66 := (Bool.xor p65 (g58 && q57))
  let q67 := (Bool.xor q57 (active && x23))
  let q68 := (Bool.xor x13 (active && x23))
  let q69 := (Bool.xor q17 (active && q68))
  let q70 := (Bool.xor q67 (active && q16))
  let q71 := (Bool.xor q70 (active && q6))
  let q72 := (Bool.xor q68 (active && q69))
  let q73 := (Bool.xor q71 (active && q12))
  let q74 := (Bool.xor q32 (active && q73))
  [q56, q6, q35, q39, q12, q1, q23, q69, q72, q55, q14, q10, x23, q73, q34, q74, q16, c257, c258, c259, c419, c22, c2, p66]

set_option maxHeartbeats 6000000 in
theorem actual_22476_22553 (x0 x3 x4 x5 x6 x7 x11 x12 x13 x15 x17 x19 x23 x25 x30 x33 x34 c257 c258 c259 c419 c9801 c78893 active phase m : Bool) :
    old22476 x0 x3 x4 x5 x6 x7 x11 x12 x13 x15 x17 x19 x23 x25 x30 x33 x34 c257 c258 c259 c419 c9801 c78893 active phase m = new22476 x0 x3 x4 x5 x6 x7 x11 x12 x13 x15 x17 x19 x23 x25 x30 x33 x34 c257 c258 c259 c419 c9801 c78893 active phase m := by
  simp only [old22476, new22476]
  bv_decide

end GVQCCV10
