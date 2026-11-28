import Init

/-! V4 conditional-context carry bridge.
The context h is a stable Boolean function of the retained data, not an
extra physical qubit. These algebraic laws do not prove full invsqrt
reachability, numerical accuracy, or the native KMB verifier contract. -/
namespace GVQCC.CarryContextBridge

def bx (a b : Bool) : Bool := Bool.xor a b

def majority (a b c : Bool) : Bool :=
  bx (bx (a && b) (a && c)) (b && c)

def measuredABI (a b c : Bool) : Bool × Bool × Bool :=
  (a, bx a (bx b c), majority a b c)

/-- CX b,c; toggle a by h; CCX c,a,b; undo h; CX a,c; SWAP b,c. -/
def bridge (a b c h : Bool) : Bool × Bool × Bool :=
  let p := bx b c
  let u := bx a h
  let k := bx b (p && u)
  (bx u h, bx a p, k)

def bridgeInverse (a sum k h : Bool) : Bool × Bool × Bool :=
  let p := bx a sum
  let b := bx k (p && bx a h)
  (a,b,bx b p)

/-- Context only needs to reveal b on the ambiguous fiber. -/
theorem bridge_correct (a b c h : Bool) :
    (bx b c = true → h = b) →
    bridge a b c h = measuredABI a b c := by
  cases a <;> cases b <;> cases c <;> cases h <;> decide

theorem bridge_inverse (a b c h : Bool) :
    let y := bridge a b c h
    bridgeInverse y.1 y.2.1 y.2.2 h = (a,b,c) := by
  cases a <;> cases b <;> cases c <;> cases h <;> decide

/-- No unconditioned reversible three-bit implementation of this ABI. -/
theorem collision_zero :
    measuredABI false true false = measuredABI false false true := by decide

theorem collision_one :
    measuredABI true true false = measuredABI true false true := by decide

/-- Restore a dirty target by measurement and an affine post-value.
The random phase is compensated for both outcomes, not postselected. -/
def restorePhase (old a b desired p m : Bool) : Bool :=
  bx (bx p (m && old)) (m && bx desired (a && b))

theorem dirty_restore_phase (old a b desired p m : Bool) :
    desired = bx old (a && b) →
    restorePhase old a b desired p m = p := by
  cases old <;> cases a <;> cases b <;> cases desired <;>
    cases p <;> cases m <;> decide

/-- One rank-one quadratic h, computed into and uncomputed from a dirty
operand, costs 1 + 2*1 CCX. The previous cubic shear costs 1 + 4. -/
def bridgeCCX (quadraticRank : Nat) : Nat := 1 + 2 * quadraticRank
theorem rank_one_bridge_cost : bridgeCCX 1 = 3 := by decide
theorem seven_bridge_saving : 7 * 5 - 7 * bridgeCCX 1 = 14 := by decide

/-- Source context at 9630: h = 1 XOR q7 XOR
(q7 XOR q14)*q29. This is the rank-one factorization identity, not
the reachability claim h=b on the real trace. -/
theorem context_9630_factor (x y z : Bool) :
    bx (bx (bx true x) (x && z)) (y && z) =
      bx (bx true x) (bx x y && z) := by
  cases x <;> cases y <;> cases z <;> decide

end GVQCC.CarryContextBridge
