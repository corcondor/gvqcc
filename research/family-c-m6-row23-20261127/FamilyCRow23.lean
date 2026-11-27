import Init
namespace GVQCC.FamilyCRow23
set_option maxRecDepth 100000
set_option maxHeartbeats 0

def bx (a b : Bool) : Bool := Bool.xor a b
def bit (v : Nat) (i : Nat) : Bool := v.testBit i

def g (v : Nat) (p : Bool) : Bool :=
  (bx (bx (bit v 2) (bit v 3)) (bit v 4)) && bx (bit v 5) p

def recover (v : Nat) (p : Bool) : Bool :=
  bx (bx (bit v 3) (g v p))
    (bx (bit v 4) (g v p) && bx (bit v 3) p)

def step (r d : Int) : Int := if r < 0 then r + d else r - d

-- Floor U / 2^16 = h; all early signs are preserved by floor division.
theorem initial_scale (u v : Int) :
    (17179869184 + 128*u - (129+2*v)*67108864) / 8388608 =
    2048 + u / 65536 - 8*(129+2*v) := by omega

-- Kernel-checked finite theorem, not native_decide or a sampled assertion.
-- The previous nonnegative remainder guard is part of the theorem.
theorem row23_recovery :
    ∀ (v : Fin 64) (j : Fin 32),
      let d : Int := 129 + 2 * (v.val : Int)
      let h : Int := (j.val : Int) - 16
      let a := 2048 + h - 8*d
      let b := a - 4*d
      let c := step b (2*d)
      let e := step c d
      0 <= a → decide (c < 0) = recover v.val (decide (e < 0)) := by decide

-- The XOR-update of the removed digit, with its original value supplied.
theorem clear_digit (s f : Bool) (h : s = f) : bx s f = false := by
  subst s
  cases f <;> decide

-- An explicit MAJ sweep stores a carry in the source bit. Its inverse UMA
-- restores source and carry and writes the full-adder sum.
def maj (a b c : Bool) := bx c (bx c a && bx c b)
def sum (a b c : Bool) := bx (bx a b) c

def sweep (a b c : Bool) : Bool × Bool × Bool :=
  let x := bx c a
  let y := bx b a
  let z := bx a (x && y)
  (z,y,x)

def unwind (z y x : Bool) : Bool × Bool × Bool :=
  let a := bx z (x && y)
  let c := bx x a
  let s := bx y c
  (a,s,c)

theorem maj_sweep (a b c : Bool) : (sweep a b c).1 = maj a b c := by
  cases a <;> cases b <;> cases c <;> decide

theorem uma_restores (a b c : Bool) :
    let (z,y,x) := sweep a b c
    unwind z y x = (a,sum a b c,c) := by
  cases a <;> cases b <;> cases c <;> decide

theorem full_adder_value (a b c : Bool) :
    a.toNat + b.toNat + c.toNat =
      (sum a b c).toNat + 2 * (maj a b c).toNat := by
  cases a <;> cases b <;> cases c <;> decide

-- Source suffix [1,0] needs no materialized 1 and no fresh carry:
-- xor top with b OR c, xor b with NOT c.
theorem suffix_top (b c : Bool) :
    maj true b c = bx (bx b c) (b && c) := by
  cases b <;> cases c <;> decide

theorem suffix_value (b t c : Bool) :
    (b.toNat + 2*t.toNat + 1 + c.toNat) % 4 =
    (bx (bx b true) c).toNat +
      2 * (bx t (bx (bx b c) (b && c))).toNat := by
  cases b <;> cases t <;> cases c <;> decide

theorem low_alias (b : Bool) :
    maj true b false = b ∧ sum true b false = !b := by
  cases b <;> decide

-- The first scratch product is erased by HMR on a live affine chart.
theorem and_hmr (a b m : Bool) :
    bx (m && (a && b)) (m && (a && b)) = false := by
  cases a <;> cases b <;> cases m <;> decide

end GVQCC.FamilyCRow23
#print axioms GVQCC.FamilyCRow23.initial_scale
#print axioms GVQCC.FamilyCRow23.row23_recovery
#print axioms GVQCC.FamilyCRow23.clear_digit
#print axioms GVQCC.FamilyCRow23.maj_sweep
#print axioms GVQCC.FamilyCRow23.uma_restores
#print axioms GVQCC.FamilyCRow23.full_adder_value
#print axioms GVQCC.FamilyCRow23.suffix_top
#print axioms GVQCC.FamilyCRow23.suffix_value
#print axioms GVQCC.FamilyCRow23.low_alias
#print axioms GVQCC.FamilyCRow23.and_hmr
