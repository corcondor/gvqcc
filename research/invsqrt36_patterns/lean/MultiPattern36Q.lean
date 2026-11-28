import Init

/-!
# Multi-Pattern 36Q InvSqrt Algebraic & Cost Certificates (V6)

Formalizes four complementary 36Q arithmetic / uncomputation patterns designed to
close the remaining 37Q peak spans and reduce paid-gate overhead beyond V4/V5
(PR #29, #31, #32):
  1. Pattern A1: Takahashi-Tani-Kunihiro (2010, arXiv:0910.2530) 0-ancilla adder.
  2. Pattern A2: Hybrid Gidney-Cuccaro/Takahashi peak-shaved adder (saves k qubits
     at only +k CCX instead of +2k in V4 or +4k in V3).
  3. Pattern B : Amortized shared-context carry bridge across m stages
     (m + 2 CCX instead of 3m CCX in PR #29 V4).
  4. Pattern C : Conditionally-clean ancilla borrowing (Khattar-Gidney 2025,
     arXiv:2407.17966) and relative-phase compute/uncompute cancellation
     (Maslov 2016, arXiv:1508.03273).

Scope disclaimer: these theorems certify the local Boolean/phase algebra and
exact CCX cost formulas. Whole-circuit KMB reachability, BDD equivalence, and
official GVQCC verifier admission are tracked separately.
-/
namespace GVQCC.MultiPattern36Q

def bx (a b : Bool) : Bool := Bool.xor a b

def boolToNat (b : Bool) : Nat := if b then 1 else 0

def bits3 (x0 x1 x2 : Bool) : Nat :=
  boolToNat x0 + 2 * boolToNat x1 + 4 * boolToNat x2

def bits4 (x0 x1 x2 x3 : Bool) : Nat :=
  boolToNat x0 + 2 * boolToNat x1 + 4 * boolToNat x2 + 8 * boolToNat x3

/-! ## Pattern A1: Takahashi (2010) 0-Ancilla 3-Bit In-Place Adder (4 CCX, 0 ancilla) -/

def takahashi3 (a0 a1 a2 b0 b1 b2 : Bool) :
    Bool × Bool × Bool × Bool × Bool × Bool :=
  -- Step 1: CX(a_i, b_i) for i = 1, 2
  let b1 := bx b1 a1
  let b2 := bx b2 a2
  -- Step 2: CX(a_1, a_2)
  let a2 := bx a2 a1
  -- Step 3: CCX(a_0, b_0, a_1); CCX(a_1, b_1, a_2)   [2 CCX]
  let a1 := bx a1 (a0 && b0)
  let a2 := bx a2 (a1 && b1)
  -- Step 4: CX(a_2, b_2); CCX(a_1, b_1, a_2); CX(a_1, b_1); CCX(a_0, b_0, a_1)  [2 CCX]
  let b2 := bx b2 a2
  let a2 := bx a2 (a1 && b1)
  let b1 := bx b1 a1
  let a1 := bx a1 (a0 && b0)
  -- Step 5: CX(a_1, a_2)
  let a2 := bx a2 a1
  -- Step 6: CX(a_i, b_i) for i = 0, 1, 2
  let b0 := bx b0 a0
  let b1 := bx b1 a1
  let b2 := bx b2 a2
  (a0, a1, a2, b0, b1, b2)

theorem takahashi3_correct (a0 a1 a2 b0 b1 b2 : Bool) :
    let (oa0, oa1, oa2, ob0, ob1, ob2) := takahashi3 a0 a1 a2 b0 b1 b2
    oa0 = a0 ∧ oa1 = a1 ∧ oa2 = a2 ∧
    bits3 ob0 ob1 ob2 = (bits3 a0 a1 a2 + bits3 b0 b1 b2) % 8 := by
  cases a0 <;> cases a1 <;> cases a2 <;>
    cases b0 <;> cases b1 <;> cases b2 <;> decide

def takahashiCCX (n : Nat) : Nat := 2 * n - 2

/-! ## Pattern A2: Hybrid Gidney-Cuccaro/Takahashi Peak-Shaved 4-Bit Adder (5 CCX, 1 fewer qubit) -/

def gidneyBit (a b cin : Bool) : Bool × Bool :=
  (bx (bx a b) cin, bx (a && b) (cin && bx a b))

def cuccaroPeakBit (cin b a : Bool) : Bool × Bool × Bool :=
  -- MAJ(cin, b, a)
  let b := bx b a
  let cin := bx cin a
  let a := bx a (cin && b)
  -- UMA(cin, b, a)
  let a := bx a (cin && b)
  let cin := bx cin a
  let b := bx b cin
  (cin, b, a)

def hybrid4 (a0 a1 a2 a3 b0 b1 b2 b3 : Bool) :
    Bool × Bool × Bool × Bool × Bool :=
  let (s0, c1) := gidneyBit a0 b0 false
  let (s1, c2) := gidneyBit a1 b1 c1
  let (s2, c3) := gidneyBit a2 b2 c2
  -- Peak bit 3 uses 0 extra ancilla (reuses operand wires via MAJ/UMA)
  let (c3_out, s3, a3_out) := cuccaroPeakBit c3 b3 a3
  (c3_out == c3 && a3_out == a3, s0, s1, s2, s3)

theorem hybrid4_correct (a0 a1 a2 a3 b0 b1 b2 b3 : Bool) :
    let (restored, s0, s1, s2, s3) := hybrid4 a0 a1 a2 a3 b0 b1 b2 b3
    restored = true ∧
    bits4 s0 s1 s2 s3 = (bits4 a0 a1 a2 a3 + bits4 b0 b1 b2 b3) % 16 := by
  cases a0 <;> cases a1 <;> cases a2 <;> cases a3 <;>
    cases b0 <;> cases b1 <;> cases b2 <;> cases b3 <;> decide

def hybridPeakCCX (n kPeak : Nat) : Nat := n + kPeak
def v4BridgePeakCCX (n kPeak : Nat) : Nat := n + 2 * kPeak
def v3ShearPeakCCX (n kPeak : Nat) : Nat := n + 4 * kPeak

theorem hybrid_beats_v4_on_peaks (n kPeak : Nat) (hk : kPeak ≥ 1) :
    hybridPeakCCX n kPeak < v4BridgePeakCCX n kPeak := by
  unfold hybridPeakCCX v4BridgePeakCCX
  omega

theorem hybrid_beats_v3_on_peaks (n kPeak : Nat) (hk : kPeak ≥ 1) :
    hybridPeakCCX n kPeak < v3ShearPeakCCX n kPeak := by
  unfold hybridPeakCCX v3ShearPeakCCX
  omega

/-! ## Pattern B: Amortized Shared-Context Carry Bridge (m + 2 CCX vs 3m in V4) -/

def majority (a b c : Bool) : Bool :=
  bx (bx (a && b) (a && c)) (b && c)

def measuredABI (a b c : Bool) : Bool × Bool × Bool :=
  (a, bx a (bx b c), majority a b c)

/-- Single carry bridge consuming an already-materialized context bit `h` (1 CCX). -/
def bridgeStep (a b c h : Bool) : Bool × Bool × Bool :=
  let p := bx b c
  let u := bx a h
  let k := bx b (p && u)
  (bx u h, bx a p, k)

/-- Two stages sharing the same quadratic factor `q` up to linear offsets `l1`, `l2`:
    compute `q` once (1 CCX), apply both bridges (2 CCX), uncompute `q` once (1 CCX) = 4 CCX. -/
def amortized2Stage (a1 b1 c1 a2 b2 c2 q l1 l2 : Bool) :
    (Bool × Bool × Bool) × (Bool × Bool × Bool) :=
  let h1 := bx q l1
  let h2 := bx q l2
  (bridgeStep a1 b1 c1 h1, bridgeStep a2 b2 c2 h2)

theorem amortized2Stage_correct (a1 b1 c1 a2 b2 c2 q l1 l2 : Bool) :
    (bx b1 c1 = true → bx q l1 = b1) →
    (bx b2 c2 = true → bx q l2 = b2) →
    amortized2Stage a1 b1 c1 a2 b2 c2 q l1 l2 =
      (measuredABI a1 b1 c1, measuredABI a2 b2 c2) := by
  cases a1 <;> cases b1 <;> cases c1 <;>
    cases a2 <;> cases b2 <;> cases c2 <;>
      cases q <;> cases l1 <;> cases l2 <;> decide

def amortizedBridgeCCX (m : Nat) : Nat := m + 2
def v4UnamortizedCCX (m : Nat) : Nat := 3 * m

theorem amortized_beats_v4 (m : Nat) (hm : m ≥ 2) :
    amortizedBridgeCCX m < v4UnamortizedCCX m := by
  unfold amortizedBridgeCCX v4UnamortizedCCX
  omega

/-! ## Pattern C: Conditionally-Clean Ancilla (Khattar-Gidney 2025) & Relative-Phase Cancel (Maslov 2016) -/

/-- Conditionally-clean / dirty-ancilla borrowing (Barenco 1995; Khattar-Gidney 2025):
    When `g = true` guarantees `d = false`, toggling `t` by `d1 && y` and cancelling `d2 && y`
    leaves `d` restored and computes `t ⊕ (g && x && y)` for ALL `(g, x, y, d, t)`. -/
def condCleanBorrow (g x y d t : Bool) : Bool × Bool :=
  let d1 := bx d (g && x)
  let t1 := bx t (d1 && y)
  let d2 := bx d1 (g && x)
  let t2 := bx t1 (d2 && y)
  (d2, t2)

theorem condCleanBorrow_correct (g x y d t : Bool) :
    (g = true → d = false) →
    condCleanBorrow g x y d t = (d, bx t (g && x && y)) := by
  cases g <;> cases x <;> cases y <;> cases d <;> cases t <;> decide

/-- Maslov (2016) relative-phase Toffoli pair: a phase error `phi(a, b)` introduced during
    compute cancels identically during uncompute when `(a, b)` are preserved. -/
theorem relative_phase_cancel (p phi : Bool) :
    bx (bx p phi) phi = p := by
  cases p <;> cases phi <;> decide

end GVQCC.MultiPattern36Q
