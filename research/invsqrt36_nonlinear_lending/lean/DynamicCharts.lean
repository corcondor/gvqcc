import Std.Tactic.BVDecide

/-! Dynamic affine/nonlinear charts. The abstract theorem proves projection for
write-only virtual coordinates; the native loan theorem certifies the actual
source interval [1860,1888) given its exact reachable-state boundary invariant.
Reachability itself is independently checked by the BDD compiler, not asserted
as a Lean proof of the whole invsqrt oracle. -/
namespace DynamicCharts

def Agree (d : Nat) (s t : Nat → Bool) : Prop :=
  ∀ q, q ≠ d → s q = t q

def xorWrite (s : Nat → Bool) (target : Nat) (value : Bool) : Nat → Bool :=
  fun q => if q = target then Bool.xor (s q) value else s q

theorem omitted_write (d : Nat) (s t : Nat → Bool) (v : Bool)
    (h : Agree d s t) : Agree d (xorWrite s d v) t := by
  intro q hq
  simpa [xorWrite, hq] using h q hq

theorem retained_write (d target : Nat) (s t : Nat → Bool) (v : Bool)
    (h : Agree d s t) : Agree d (xorWrite s target v) (xorWrite t target v) := by
  intro q hq
  by_cases ht : q = target
  · simp [xorWrite, ht, h q hq]
  · simp [xorWrite, ht, h q hq]

theorem shared_product (d a b target : Nat) (s t : Nat → Bool)
    (ha : a ≠ d) (hb : b ≠ d) (h : Agree d s t) :
    Agree d (xorWrite s target (s a && s b)) (xorWrite t target (t a && t b)) := by
  rw [h a ha, h b hb]
  exact retained_write d target s t (t a && t b) h

theorem phase_read (d a b : Nat) (s t : Nat → Bool) (p m : Bool)
    (ha : a ≠ d) (hb : b ≠ d) (h : Agree d s t) :
    Bool.xor p (m && s a && s b) = Bool.xor p (m && t a && t b) := by
  rw [h a ha, h b hb]

theorem central_nonlinear_switch (carrier missing pred affine : Bool)
    (hc : carrier = pred) (hm : missing = affine) :
    Bool.xor (Bool.xor carrier pred) affine = missing := by
  subst carrier
  subst missing
  cases pred <;> cases affine <;> decide

theorem restore_nonlinear_switch (carrier missing pred affine : Bool)
    (hc : carrier = pred) (hm : missing = affine) :
    Bool.xor (Bool.xor missing affine) pred = carrier := by
  subst carrier
  subst missing
  cases pred <;> cases affine <;> decide

theorem branch_chart_join (active original transformed : Bool)
    (h : active = true → original = transformed) :
    (if active then original else false) =
    (if active then transformed else false) := by
  cases active
  · rfl
  · simpa using h rfl

-- Actual native KMB [1860,1888), on the entry chart q34=0,
-- q18 = not(q3 AND q5). The HMR at the exit gives q33=0.
-- Entry physical q34 carries virtual q36. Exit physical q33 carries q36.
def original1860 (x3 x5 x6 x14 x20 x23 x24 x26 x32 x33 x36 m phase : Bool) : List Bool :=
  let q3_1 := x3
  let q5_1 := x5
  let q6_1 := x6
  let q14_1 := x14
  let q18_1 := (Bool.not (x3 && x5))
  let q20_1 := x20
  let q23_1 := x23
  let q24_1 := x24
  let q26_1 := x26
  let q32_1 := x32
  let q33_1 := x33
  let q34_1 := false
  let q36_1 := x36
  let q34_2 := (Bool.xor q34_1 (q32_1 && q33_1))
  let q24_2 := (Bool.xor q24_1 q33_1)
  let q34_3 := (Bool.xor q34_2 q32_1)
  let q33_2 := (Bool.xor q33_1 q32_1)
  let q24_3 := (Bool.xor q24_2 q32_1)
  let q34_4 := (Bool.xor q34_3 q26_1)
  let q24_4 := (Bool.xor q24_3 q26_1)
  let q34_5 := q24_4
  let q24_5 := q34_4
  let q34_6 := (Bool.xor q34_5 q23_1)
  let q33_3 := (Bool.xor q33_2 q23_1)
  let q24_6 := (Bool.xor q24_5 q23_1)
  let q34_7 := (Bool.xor q34_6 q14_1)
  let q33_4 := (Bool.xor q33_3 q14_1)
  let q34_8 := (Bool.not q34_7)
  let q34_9 := (Bool.xor q34_8 (q24_6 && q33_4))
  let q26_2 := (Bool.xor q26_1 q33_4)
  let q24_7 := (Bool.xor q24_6 q33_4)
  let q23_2 := (Bool.xor q23_1 q33_4)
  let q23_3 := (Bool.xor q23_2 q32_1)
  let q33_5 := (Bool.xor q33_4 q26_2)
  let q33_6 := (Bool.xor q33_5 q24_7)
  let q26_3 := q24_7
  let q24_8 := q26_2
  let q33_7 := (Bool.xor q33_6 q23_3)
  let q24_9 := q23_3
  let q23_4 := q24_8
  let q23_5 := (Bool.xor q23_4 q20_1)
  let q24_10 := (Bool.xor q24_9 q14_1)
  let q23_6 := (Bool.xor q23_5 q6_1)
  let p1 := (Bool.xor phase (q33_7 && m))
  let q33_8 := false
  [q3_1, q5_1, q6_1, q14_1, q18_1, q20_1, q23_6, q24_10, q26_3, q32_1, q34_9, q36_1, p1, m]

def loan1860 (x3 x5 x6 x14 x20 x23 x24 x26 x32 x33 x36 m phase : Bool) : List Bool :=
  let q3_1 := x3
  let q5_1 := x5
  let q6_1 := x6
  let q14_1 := x14
  let q18_1 := (Bool.not (x3 && x5))
  let q20_1 := x20
  let q23_1 := x23
  let q24_1 := x24
  let q26_1 := x26
  let q32_1 := x32
  let q33_1 := x33
  let q34_1 := x36
  let q18_2 := (Bool.xor q18_1 (q3_1 && q5_1))
  let q18_3 := (Bool.not q18_2)
  let q18_4 := q34_1
  let q34_2 := q18_3
  let q34_3 := (Bool.xor q34_2 (q32_1 && q33_1))
  let q24_2 := (Bool.xor q24_1 q33_1)
  let q34_4 := (Bool.xor q34_3 q32_1)
  let q33_2 := (Bool.xor q33_1 q32_1)
  let q24_3 := (Bool.xor q24_2 q32_1)
  let q34_5 := (Bool.xor q34_4 q26_1)
  let q24_4 := (Bool.xor q24_3 q26_1)
  let q34_6 := q24_4
  let q24_5 := q34_5
  let q34_7 := (Bool.xor q34_6 q23_1)
  let q33_3 := (Bool.xor q33_2 q23_1)
  let q24_6 := (Bool.xor q24_5 q23_1)
  let q34_8 := (Bool.xor q34_7 q14_1)
  let q33_4 := (Bool.xor q33_3 q14_1)
  let q34_9 := (Bool.not q34_8)
  let q34_10 := (Bool.xor q34_9 (q24_6 && q33_4))
  let q26_2 := (Bool.xor q26_1 q33_4)
  let q24_7 := (Bool.xor q24_6 q33_4)
  let q23_2 := (Bool.xor q23_1 q33_4)
  let q23_3 := (Bool.xor q23_2 q32_1)
  let q33_5 := (Bool.xor q33_4 q26_2)
  let q33_6 := (Bool.xor q33_5 q24_7)
  let q26_3 := q24_7
  let q24_8 := q26_2
  let q33_7 := (Bool.xor q33_6 q23_3)
  let q24_9 := q23_3
  let q23_4 := q24_8
  let q23_5 := (Bool.xor q23_4 q20_1)
  let q24_10 := (Bool.xor q24_9 q14_1)
  let q23_6 := (Bool.xor q23_5 q6_1)
  let p1 := (Bool.xor phase (q33_7 && m))
  let q33_8 := false
  let q18_5 := q33_8
  let q33_9 := q18_4
  let q18_6 := (Bool.not q18_5)
  let q18_7 := (Bool.xor q18_6 (q3_1 && q5_1))
  [q3_1, q5_1, q6_1, q14_1, q18_7, q20_1, q23_6, q24_10, q26_3, q32_1, q34_10, q33_9, p1, m]

set_option maxHeartbeats 2000000 in
theorem actual_1860_1888 (x3 x5 x6 x14 x20 x23 x24 x26 x32 x33 x36 m phase : Bool) :
    original1860 x3 x5 x6 x14 x20 x23 x24 x26 x32 x33 x36 m phase = loan1860 x3 x5 x6 x14 x20 x23 x24 x26 x32 x33 x36 m phase := by
  simp [original1860, loan1860] <;> bv_decide

end DynamicCharts
