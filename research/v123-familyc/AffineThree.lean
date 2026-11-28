import Recovery

/-! V123: exact bounded row21 affine-subspace recovery, RREF chart
semantics, and three-slot carry/measurement policy. These are local
certificates, not a refinement proof for the complete serialized KMB. -/
namespace GVQCC.FamilyCV123
set_option maxRecDepth 100000
set_option maxHeartbeats 0

def bx (a b : Bool) := Bool.xor a b

structure Cube where
  rows : List Nat
  rhs : Nat
  pivots : List Nat

def cubes : List Cube :=
  [⟨[40],1,[3]⟩, ⟨[33,36],2,[0,2]⟩, ⟨[53,88],2,[0,3]⟩,
   ⟨[21,24,64],3,[0,3,6]⟩,
   ⟨[69,72,80,96],4,[0,3,4,5]⟩,
   ⟨[5,98,8,16],2,[0,1,3,4]⟩,
   ⟨[81,70,24,96],5,[0,1,3,5]⟩,
   ⟨[1,98,4,40,16],2,[0,1,2,3,4]⟩]

def parity (x a : Nat) : Bool :=
  (List.range 7).foldl (fun s i => bx s (x.testBit i && a.testBit i)) false

def indicator (x rhs : Nat) : List Nat → Bool
  | [] => true
  | a::as => (parity x a == rhs.testBit 0) && indicator x (rhs/2) as

def recover (x : Nat) : Bool :=
  cubes.foldl (fun s c => bx s (indicator x c.rhs c.rows)) false

theorem recover_table :
    ∀ x : Fin 128, GVQCC.FamilyCV122.care.testBit x.val = true →
      recover x.val = GVQCC.FamilyCV122.table.testBit x.val := by decide

theorem row21_reconstruction (v : Fin 64) (h : Fin 128)
    (hg : 0 ≤ GVQCC.FamilyCV122.r26 (v.val : Int) ((h.val : Int)-64)) :
    recover (2*v.val + (if GVQCC.FamilyCV122.r21 (v.val : Int) ((h.val : Int)-64) < 0 then 1 else 0)) =
    decide (GVQCC.FamilyCV122.r22 (v.val : Int) ((h.val : Int)-64) < 0) := by
  have ht := GVQCC.FamilyCV122.row21_table v h hg
  let idx := 2*v.val + (if GVQCC.FamilyCV122.r21 (v.val : Int) ((h.val : Int)-64) < 0 then 1 else 0)
  have hv := v.isLt
  have hi : idx < 128 := by
    dsimp only [idx]
    split <;> omega
  exact (recover_table ⟨idx,hi⟩ ht.1).trans ht.2

-- RREF implementation: each nonpivot input is unchanged. Parities are
-- formed directly on pivot wires, used as controls and then reversed.
def cnot (x : Nat) (g : Nat × Nat) : Nat :=
  if x.testBit g.1 then Nat.xor x (2^g.2) else x

def chartGates (c : Cube) : List (Nat × Nat) :=
  (c.rows.zip c.pivots).flatMap fun (a,p) =>
    (List.range 7).filterMap fun i =>
      if i != p && a.testBit i then some (i,p) else none

def chart (c : Cube) (x : Nat) : Nat :=
  (chartGates c).foldl cnot x

def chartIndicator (x rhs : Nat) : List Nat → Bool
  | [] => true
  | p::ps => (x.testBit p == rhs.testBit 0) && chartIndicator x (rhs/2) ps

theorem chart_exact :
    ∀ x : Fin 128, cubes.all (fun c =>
      (chartIndicator (chart c x.val) c.rhs c.pivots ==
       indicator x.val c.rhs c.rows) &&
      decide ((chartGates c).reverse.foldl cnot (chart c x.val) = x.val)) = true := by decide

def cubeCost (c : Cube) : Nat :=
  match c.rows.length with
  | 0 | 1 => 0
  | 2 => 1
  | 3 => 2
  | 4 => 3
  | 5 => 5
  | _ => 1000

theorem recovery_paid : (cubes.map cubeCost).foldl Nat.add 0 = 18 := by decide

/-- Row retirement: the logical bit is reconstructed before the deferred
X-measurement debt is repaid. Intervening usage must preserve this value
under the reverse computation; not an arbitrary unitary commutation rule. -/
theorem delayed_phase (s restored m phase : Bool) (h : restored = s) :
    bx (bx phase (m && s)) (m && restored) = phase := by
  subst restored
  cases s <;> cases m <;> cases phase <;> decide

/-- Five-control operation with two clean temporaries, including early
release/recomputation of the first AND. Arbitrary target and outcomes. -/
theorem five_control_phase (a b c d e z m1 m2 m3 m4 : Bool) :
    let t := a && b
    let u := t && c
    let w := d && e
    let z' := bx z (u && w)
    let tr := a && b
    let p1 := bx (m1 && t) (m1 && (a && b))
    let p2 := bx (m2 && w) (m2 && (d && e))
    let p3 := bx (m3 && u) (m3 && (tr && c))
    let p4 := bx (m4 && tr) (m4 && (a && b))
    (z' = bx z (a && b && c && d && e)) ∧
      bx (bx p1 p2) (bx p3 p4) = false := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases e <;>
  cases z <;> cases m1 <;> cases m2 <;> cases m3 <;> cases m4 <;> decide

def carry (a s c : Bool) : Bool := bx c (bx a c && bx a s)
theorem carry_debt (a s c m : Bool) :
    bx (m && carry a s c)
      (bx (m && c) (m && (bx a c && bx a s))) = false := by
  cases a <;> cases s <;> cases c <;> cases m <;> decide

-- Independent abstract schedule certificate. A carry is either live,
-- a ghost with an unpaid phase, or absent. Root carry is always available.
inductive Move where
  | place (k : Nat)
  | remove (k : Nat)
  | ghost (k : Nat) (m : Bool)
  | repay (k : Nat)
  | top

structure State where
  live : Nat
  debt : Nat
  paid : Nat
  topDone : Bool

def setBit (x k : Nat) := Nat.xor x (2^k)
def predecessor (s : State) (k : Nat) : Bool :=
  (k == 1) || s.live.testBit (k-1)
def occupancy (x : Nat) : Nat :=
  ((List.range 7).filter (fun k => x.testBit k)).length

def transition (s : State) (op : Move) : Option State :=
  match op with
  | .place k =>
    if predecessor s k && !s.live.testBit k && decide (occupancy s.live < 3) then
      some {s with live := setBit s.live k, paid := s.paid+1}
    else none
  | .remove k =>
    if predecessor s k && s.live.testBit k then
      some {s with live := setBit s.live k}
    else none
  | .ghost k m =>
    if s.live.testBit k && !s.debt.testBit k then
      some {s with live := setBit s.live k,
                   debt := if m then setBit s.debt k else s.debt}
    else none
  | .repay k =>
    if predecessor s k && s.debt.testBit k then
      some {s with debt := setBit s.debt k}
    else none
  | .top =>
    if s.live.testBit 6 && !s.topDone then
      some {s with topDone := true, paid := s.paid+1}
    else none

def trace (s : State) : List Move → Option State
  | [] => some s
  | op::ops => match transition s op with
    | none => none
    | some t => trace t ops

def policy (m5 m3 : Bool) : List Move :=
  [.place 1,.place 2,.place 3,.remove 2,.place 4,.remove 1,
   .place 5,.remove 4,.place 6,.top,.remove 6,.ghost 5 m5] ++
  (if m5 then [.place 4,.repay 5,.remove 4] else []) ++
  [.ghost 3 m3] ++
  (if m3 then [.place 1,.place 2,.repay 3,.remove 2,.remove 1] else [])

def receipt (m5 m3 : Bool) : Bool :=
  match trace ⟨0,0,0,false⟩ (policy m5 m3) with
  | none => false
  | some s => (s.live == 0) && (s.debt == 0) && s.topDone &&
    (s.paid == 7 + (if m5 then 1 else 0) + (if m3 then 2 else 0))

theorem three_slot_all_branches : ∀ m5 m3 : Bool, receipt m5 m3 = true := by decide

def price (m5 m3 : Bool) : Nat :=
  match trace ⟨0,0,0,false⟩ (policy m5 m3) with
  | none => 1000
  | some s => s.paid

theorem expected_numerator : price false false + price false true +
    price true false + price true true = 34 := by decide

end GVQCC.FamilyCV123

#print axioms GVQCC.FamilyCV123.recover_table
#print axioms GVQCC.FamilyCV123.row21_reconstruction
#print axioms GVQCC.FamilyCV123.chart_exact
#print axioms GVQCC.FamilyCV123.recovery_paid
#print axioms GVQCC.FamilyCV123.delayed_phase
#print axioms GVQCC.FamilyCV123.five_control_phase
#print axioms GVQCC.FamilyCV123.carry_debt
#print axioms GVQCC.FamilyCV123.three_slot_all_branches
#print axioms GVQCC.FamilyCV123.expected_numerator
