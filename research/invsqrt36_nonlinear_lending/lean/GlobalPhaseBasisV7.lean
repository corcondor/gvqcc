import Std.Tactic.BVDecide

/-! Concrete phase-factorization certificates from V7 union native instruction
offsets (half-open ranges in v7union parent), not a complete oracle proof.
All free Boolean variables are unrestricted. The classical guard may be arbitrary.
The three guarded bodies have static costs 8→1, 2→0, 7→1.
-/
namespace GVQCCV7
def bx := Bool.xor

-- Parent offset 17223; native guarded body gate lists, operands in physical order.
-- OLD [[32,0,6],[48,0,1,6],[32,0,18],[48,0,1,18],[32,0,22],[48,0,1,22],[32,0,25],[48,0,1,25],[32,0,30],[48,0,1,30],[32,0,31],[48,0,1,31],[32,0,33],[48,0,1,33],[32,0,34],[48,0,1,34]]
-- NEW [[33,18,6],[33,22,6],[33,25,6],[33,30,6],[33,31,6],[33,33,6],[33,34,6],[48,0,1,6],[33,34,6],[33,33,6],[33,31,6],[33,30,6],[33,25,6],[33,22,6],[33,18,6],[32,0,6],[32,0,18],[32,0,22],[32,0,25],[32,0,30],[32,0,31],[32,0,33],[32,0,34]]
def old_17223_phase (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s : Bool) : Bool :=
  let p0 := bx s (m && x0 && x6)
  let p1 := bx p0 (m && x0 && x1 && x6)
  let p2 := bx p1 (m && x0 && x18)
  let p3 := bx p2 (m && x0 && x1 && x18)
  let p4 := bx p3 (m && x0 && x22)
  let p5 := bx p4 (m && x0 && x1 && x22)
  let p6 := bx p5 (m && x0 && x25)
  let p7 := bx p6 (m && x0 && x1 && x25)
  let p8 := bx p7 (m && x0 && x30)
  let p9 := bx p8 (m && x0 && x1 && x30)
  let p10 := bx p9 (m && x0 && x31)
  let p11 := bx p10 (m && x0 && x1 && x31)
  let p12 := bx p11 (m && x0 && x33)
  let p13 := bx p12 (m && x0 && x1 && x33)
  let p14 := bx p13 (m && x0 && x34)
  let p15 := bx p14 (m && x0 && x1 && x34)
  p15

def old_17223_restored (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s : Bool) : Bool :=
  let p0 := bx s (m && x0 && x6)
  let p1 := bx p0 (m && x0 && x1 && x6)
  let p2 := bx p1 (m && x0 && x18)
  let p3 := bx p2 (m && x0 && x1 && x18)
  let p4 := bx p3 (m && x0 && x22)
  let p5 := bx p4 (m && x0 && x1 && x22)
  let p6 := bx p5 (m && x0 && x25)
  let p7 := bx p6 (m && x0 && x1 && x25)
  let p8 := bx p7 (m && x0 && x30)
  let p9 := bx p8 (m && x0 && x1 && x30)
  let p10 := bx p9 (m && x0 && x31)
  let p11 := bx p10 (m && x0 && x1 && x31)
  let p12 := bx p11 (m && x0 && x33)
  let p13 := bx p12 (m && x0 && x1 && x33)
  let p14 := bx p13 (m && x0 && x34)
  let p15 := bx p14 (m && x0 && x1 && x34)
  (x0 == x0) && (x1 == x1) && (x6 == x6) && (x18 == x18) && (x22 == x22) && (x25 == x25) && (x30 == x30) && (x31 == x31) && (x33 == x33) && (x34 == x34)

def new_17223_phase (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s : Bool) : Bool :=
  let v6_0 := bx x6 (m && x18)
  let v6_1 := bx v6_0 (m && x22)
  let v6_2 := bx v6_1 (m && x25)
  let v6_3 := bx v6_2 (m && x30)
  let v6_4 := bx v6_3 (m && x31)
  let v6_5 := bx v6_4 (m && x33)
  let v6_6 := bx v6_5 (m && x34)
  let p7 := bx s (m && x0 && x1 && v6_6)
  let v6_8 := bx v6_6 (m && x34)
  let v6_9 := bx v6_8 (m && x33)
  let v6_10 := bx v6_9 (m && x31)
  let v6_11 := bx v6_10 (m && x30)
  let v6_12 := bx v6_11 (m && x25)
  let v6_13 := bx v6_12 (m && x22)
  let v6_14 := bx v6_13 (m && x18)
  let p15 := bx p7 (m && x0 && v6_14)
  let p16 := bx p15 (m && x0 && x18)
  let p17 := bx p16 (m && x0 && x22)
  let p18 := bx p17 (m && x0 && x25)
  let p19 := bx p18 (m && x0 && x30)
  let p20 := bx p19 (m && x0 && x31)
  let p21 := bx p20 (m && x0 && x33)
  let p22 := bx p21 (m && x0 && x34)
  p22

def new_17223_restored (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s : Bool) : Bool :=
  let v6_0 := bx x6 (m && x18)
  let v6_1 := bx v6_0 (m && x22)
  let v6_2 := bx v6_1 (m && x25)
  let v6_3 := bx v6_2 (m && x30)
  let v6_4 := bx v6_3 (m && x31)
  let v6_5 := bx v6_4 (m && x33)
  let v6_6 := bx v6_5 (m && x34)
  let p7 := bx s (m && x0 && x1 && v6_6)
  let v6_8 := bx v6_6 (m && x34)
  let v6_9 := bx v6_8 (m && x33)
  let v6_10 := bx v6_9 (m && x31)
  let v6_11 := bx v6_10 (m && x30)
  let v6_12 := bx v6_11 (m && x25)
  let v6_13 := bx v6_12 (m && x22)
  let v6_14 := bx v6_13 (m && x18)
  let p15 := bx p7 (m && x0 && v6_14)
  let p16 := bx p15 (m && x0 && x18)
  let p17 := bx p16 (m && x0 && x22)
  let p18 := bx p17 (m && x0 && x25)
  let p19 := bx p18 (m && x0 && x30)
  let p20 := bx p19 (m && x0 && x31)
  let p21 := bx p20 (m && x0 && x33)
  let p22 := bx p21 (m && x0 && x34)
  (x0 == x0) && (x1 == x1) && (v6_14 == x6) && (x18 == x18) && (x22 == x22) && (x25 == x25) && (x30 == x30) && (x31 == x31) && (x33 == x33) && (x34 == x34)

theorem actual_17223_phase (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s : Bool) :
    old_17223_phase x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s = new_17223_phase x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s := by
  unfold old_17223_phase new_17223_phase bx
  bv_decide

theorem old_17223_restores (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s : Bool) :
    old_17223_restored x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s = true := by
  unfold old_17223_restored bx
  bv_decide

theorem new_17223_restores (x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s : Bool) :
    new_17223_restored x0 x1 x6 x18 x22 x25 x30 x31 x33 x34 m s = true := by
  unfold new_17223_restored bx
  bv_decide


-- Parent offset 21430; native guarded body gate lists, operands in physical order.
-- OLD [[49,24,35,33],[33,24,33],[33,2,33],[16,33],[49,24,35,33],[33,24,33],[33,2,33]]
-- NEW [[16,2],[16,24],[16,33],[32,24,35]]
def old_21430_phase (x2 x24 x33 x35 m s : Bool) : Bool :=
  let v33_0 := bx x33 (m && x24 && x35)
  let v33_1 := bx v33_0 (m && x24)
  let v33_2 := bx v33_1 (m && x2)
  let p3 := bx s (m && v33_2)
  let v33_4 := bx v33_2 (m && x24 && x35)
  let v33_5 := bx v33_4 (m && x24)
  let v33_6 := bx v33_5 (m && x2)
  p3

def old_21430_restored (x2 x24 x33 x35 m s : Bool) : Bool :=
  let v33_0 := bx x33 (m && x24 && x35)
  let v33_1 := bx v33_0 (m && x24)
  let v33_2 := bx v33_1 (m && x2)
  let p3 := bx s (m && v33_2)
  let v33_4 := bx v33_2 (m && x24 && x35)
  let v33_5 := bx v33_4 (m && x24)
  let v33_6 := bx v33_5 (m && x2)
  (x2 == x2) && (x24 == x24) && (v33_6 == x33) && (x35 == x35)

def new_21430_phase (x2 x24 x33 x35 m s : Bool) : Bool :=
  let p0 := bx s (m && x2)
  let p1 := bx p0 (m && x24)
  let p2 := bx p1 (m && x33)
  let p3 := bx p2 (m && x24 && x35)
  p3

def new_21430_restored (x2 x24 x33 x35 m s : Bool) : Bool :=
  let p0 := bx s (m && x2)
  let p1 := bx p0 (m && x24)
  let p2 := bx p1 (m && x33)
  let p3 := bx p2 (m && x24 && x35)
  (x2 == x2) && (x24 == x24) && (x33 == x33) && (x35 == x35)

theorem actual_21430_phase (x2 x24 x33 x35 m s : Bool) :
    old_21430_phase x2 x24 x33 x35 m s = new_21430_phase x2 x24 x33 x35 m s := by
  unfold old_21430_phase new_21430_phase bx
  bv_decide

theorem old_21430_restores (x2 x24 x33 x35 m s : Bool) :
    old_21430_restored x2 x24 x33 x35 m s = true := by
  unfold old_21430_restored bx
  bv_decide

theorem new_21430_restores (x2 x24 x33 x35 m s : Bool) :
    new_21430_restored x2 x24 x33 x35 m s = true := by
  unfold new_21430_restored bx
  bv_decide


-- Parent offset 35292; native guarded body gate lists, operands in physical order.
-- OLD [[32,17,20],[48,17,19,20],[48,17,20,25],[32,19,20],[48,17,19,20],[48,19,20,25],[48,17,20,21],[48,19,20,21],[48,20,21,25]]
-- NEW [[33,19,17],[33,25,17],[33,25,21],[48,20,17,21],[33,25,21],[33,25,17],[33,19,17],[32,20,25],[32,17,20],[32,19,20]]
def old_35292_phase (x17 x19 x20 x21 x25 m s : Bool) : Bool :=
  let p0 := bx s (m && x17 && x20)
  let p1 := bx p0 (m && x17 && x19 && x20)
  let p2 := bx p1 (m && x17 && x20 && x25)
  let p3 := bx p2 (m && x19 && x20)
  let p4 := bx p3 (m && x17 && x19 && x20)
  let p5 := bx p4 (m && x19 && x20 && x25)
  let p6 := bx p5 (m && x17 && x20 && x21)
  let p7 := bx p6 (m && x19 && x20 && x21)
  let p8 := bx p7 (m && x20 && x21 && x25)
  p8

def old_35292_restored (x17 x19 x20 x21 x25 m s : Bool) : Bool :=
  let p0 := bx s (m && x17 && x20)
  let p1 := bx p0 (m && x17 && x19 && x20)
  let p2 := bx p1 (m && x17 && x20 && x25)
  let p3 := bx p2 (m && x19 && x20)
  let p4 := bx p3 (m && x17 && x19 && x20)
  let p5 := bx p4 (m && x19 && x20 && x25)
  let p6 := bx p5 (m && x17 && x20 && x21)
  let p7 := bx p6 (m && x19 && x20 && x21)
  let p8 := bx p7 (m && x20 && x21 && x25)
  (x17 == x17) && (x19 == x19) && (x20 == x20) && (x21 == x21) && (x25 == x25)

def new_35292_phase (x17 x19 x20 x21 x25 m s : Bool) : Bool :=
  let v17_0 := bx x17 (m && x19)
  let v17_1 := bx v17_0 (m && x25)
  let v21_2 := bx x21 (m && x25)
  let p3 := bx s (m && x20 && v17_1 && v21_2)
  let v21_4 := bx v21_2 (m && x25)
  let v17_5 := bx v17_1 (m && x25)
  let v17_6 := bx v17_5 (m && x19)
  let p7 := bx p3 (m && x20 && x25)
  let p8 := bx p7 (m && v17_6 && x20)
  let p9 := bx p8 (m && x19 && x20)
  p9

def new_35292_restored (x17 x19 x20 x21 x25 m s : Bool) : Bool :=
  let v17_0 := bx x17 (m && x19)
  let v17_1 := bx v17_0 (m && x25)
  let v21_2 := bx x21 (m && x25)
  let p3 := bx s (m && x20 && v17_1 && v21_2)
  let v21_4 := bx v21_2 (m && x25)
  let v17_5 := bx v17_1 (m && x25)
  let v17_6 := bx v17_5 (m && x19)
  let p7 := bx p3 (m && x20 && x25)
  let p8 := bx p7 (m && v17_6 && x20)
  let p9 := bx p8 (m && x19 && x20)
  (v17_6 == x17) && (x19 == x19) && (x20 == x20) && (v21_4 == x21) && (x25 == x25)

theorem actual_35292_phase (x17 x19 x20 x21 x25 m s : Bool) :
    old_35292_phase x17 x19 x20 x21 x25 m s = new_35292_phase x17 x19 x20 x21 x25 m s := by
  unfold old_35292_phase new_35292_phase bx
  bv_decide

theorem old_35292_restores (x17 x19 x20 x21 x25 m s : Bool) :
    old_35292_restored x17 x19 x20 x21 x25 m s = true := by
  unfold old_35292_restored bx
  bv_decide

theorem new_35292_restores (x17 x19 x20 x21 x25 m s : Bool) :
    new_35292_restored x17 x19 x20 x21 x25 m s = true := by
  unfold new_35292_restored bx
  bv_decide

-- Parent [35136,35174): seven arbitrary guards, six basis polynomials.
-- a,b,c,e,f,g,d are q18,q19,q20,q21,q25,q33,q35.
def parity (a b c : Bool) := bx (bx a b) c
def p1 (e g d : Bool) := d && bx e g
def p2 (a f g d : Bool) := d && parity a f g
def p3 (e f g d : Bool) := d && parity e f g
def p4 (a b c f g d : Bool) := d && parity a (bx (b && c) (c && f)) g
def p5 (b c f d : Bool) := d && parity c f (bx (b && c) (c && f))
def p6 (b c f g d : Bool) := d && parity c g (bx (b && c) (c && f))
def phaseOld (a b c e f g d r0 r1 r2 r3 r4 r5 r6 : Bool) :=
  bx (bx (bx (r0 && (d && parity f g (bx (b && c) (c && f))))
    (r1 && p3 e f g d)) (bx (r2 && p5 b c f d) (r3 && p1 e g d)))
    (bx (bx (r4 && p4 a b c f g d) (r5 && p6 b c f g d)) (r6 && p2 a f g d))
def phaseNew (a b c e f g d r0 r1 r2 r3 r4 r5 r6 : Bool) :=
  bx (bx (bx (bx r0 r3 && p1 e g d) (bx r0 r6 && p2 a f g d))
    (bx r0 r1 && p3 e f g d))
    (bx (bx (bx r0 r4 && p4 a b c f g d) (bx r0 r2 && p5 b c f d))
        (bx r0 r5 && p6 b c f g d))
theorem actual_35136_phase_basis (a b c e f g d r0 r1 r2 r3 r4 r5 r6 : Bool) :
    phaseOld a b c e f g d r0 r1 r2 r3 r4 r5 r6 =
    phaseNew a b c e f g d r0 r1 r2 r3 r4 r5 r6 := by
  unfold phaseOld phaseNew p1 p2 p3 p4 p5 p6 parity bx
  bv_decide

-- Entry carrier polynomial used at original [8096,8159).
def carrier (a b c d : Bool) :=
  bx (bx (bx (bx (bx (bx b c) (a && b)) (a && c)) (a && d)) (b && c)) (b && d)
theorem carrier_one_and (a b c d : Bool) :
    carrier a b c d = bx c (bx a b && bx c (bx b d)) := by
  unfold carrier bx
  bv_decide

-- HMR move: correction uses an exact reachable entry expression.
-- Original terminal outcome m is preserved, fresh outcome n contributes zero.
theorem terminal_phase_move (h m n t s : Bool) :
    bx (bx (bx (bx (bx s (m && h)) (m && h)) (m && t)) (n && h)) (n && h)
      = bx s (m && t) := by
  unfold bx
  bv_decide

theorem static_three_bodies : (8 + 2 + 7 : Nat) - (1 + 0 + 1) = 15 := by decide
end GVQCCV7
