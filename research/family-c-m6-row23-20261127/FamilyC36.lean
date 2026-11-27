import Init
namespace GVQCC.FamilyC36
set_option maxRecDepth 100000
set_option maxHeartbeats 0

def bx (a b : Bool) := Bool.xor a b
def bit (v i : Nat) := v.testBit i
def step (r d : Int) := if r < 0 then r + d else r - d
def t (a s : Bool) (v : Nat) : Nat → Bool
  | 0 => bx a s && !(bx (bit v 0) s)
  | n+1 => t a s v n && !(bx (bit v (n+1)) (bit v 0))

def ladderWord (a s : Bool) (v : Nat) : Nat :=
  (!a).toNat + 2 * (!(bx (bit v 0) (bx a s))).toNat +
  4 * (!(bx (bit v 1) (t a s v 0))).toNat +
  8 * (!(bx (bit v 2) (t a s v 1))).toNat +
  16 * (!(bx (bit v 3) (t a s v 2))).toNat +
  32 * (!(bx (bit v 4) (t a s v 3))).toNat +
  64 * (!(bx (bit v 5) (t a s v 4))).toNat +
  128 * (t a s v 5).toNat

theorem first_row_ladder :
    ∀ (v : Fin 64) (a s : Bool),
      (ladderWord a s v.val : Int) =
      ((a.toNat : Int) + 254*(s.toNat : Int) - (129+2*(v.val : Int))) % 256 := by decide

theorem first_row_truncated :
    ∀ (v : Fin 64) (a s : Bool),
      ((ladderWord a s v.val : Int) % 128) =
      ((a.toNat : Int) + 254*(s.toNat : Int) - (129+2*(v.val : Int))) % 128 := by decide

-- The omitted top bit of R26 cannot influence lower bits of R25.
theorem row25_low_identity :
    ∀ (v : Fin 64) (a s l : Bool),
      (2*((ladderWord a s v.val : Int) % 128) +
        (l.toNat : Int) - (129+2*(v.val : Int))) % 256 =
      (125+(l.toNat : Int)+2*(a.toNat : Int)-4*(s.toNat : Int)-6*(v.val : Int)) % 256 := by decide

def s24pre (v : Nat) (a : Bool) := bx (bit v 5) (a && bit v 4)
def s24post (v : Nat) (p : Bool) := bx (bx (bit v 5) (bit v 4)) (p && bit v 4)
def lowFrame (r : Int) (s : Bool) : Int :=
  r / 256 * 256 + (if s then r % 256 else 255 - r % 256)

-- For any admissible bounded high-word chart the virtual control is correct:
-- complement only the lower eight bits, add d, unframe using the post-row
-- sign. The top bit is never framed and the omitted old sign is not a wire.
theorem virtual_row24 :
    ∀ (v : Fin 64) (j : Fin 16),
      let d : Int := 129+2*(v.val : Int)
      let h : Int := (j.val : Int)-8
      let z : Int := 250+h-12*(v.val : Int)
      let r := z % 512
      let s := s24pre v.val (decide (256 <= r))
      let mid := (lowFrame r s + d) % 512
      let p := decide (256 <= mid)
      let w := step z d
      0 <= z + 2*d →
        s = decide (z < 0) ∧
        s24post v.val p = s ∧
        lowFrame mid (s24post v.val p) = w % 512 ∧
        p = decide (w < 0) := by decide

-- Expansion of the two-AND row23 formula for a scratchless XOR write.
theorem expand_row23 (v2 v3 v4 v5 p : Bool) :
    let g := (bx (bx v2 v3) v4) && bx v5 p
    bx (bx v3 g) (bx v4 g && bx v3 p) =
    bx (bx v3 (v4 && bx v3 p))
      (g && !(bx v3 p)) := by
  cases v2 <;> cases v3 <;> cases v4 <;> cases v5 <;> cases p <;> decide

-- A dirty borrowed bit implements a triple product with four CCXs.
-- No assumption that the borrowed bit or target starts at zero.
theorem dirty_triple (a b c q z : Bool) :
    let q1 := bx q (a && b)
    let z1 := bx z (q1 && c)
    let q2 := bx q1 (a && b)
    let z2 := bx z1 (q2 && c)
    q2 = q ∧ z2 = bx z (a && b && c) := by
  cases a <;> cases b <;> cases c <;> cases q <;> cases z <;> decide

theorem cx_involutive (a b : Bool) : bx a (bx a b) = b := by
  cases a <;> cases b <;> decide

-- Invertible six-bit chart: base inputs are v1..v5,p.
def chart22 (x : Nat) (i : Nat) : Bool :=
  let mask := ([45,30,34,8,24,38] : List Nat)[i]!
  let raw := ((List.range 6).foldl (fun b j => bx b (bit mask j && bit x j)) false)
  bx raw (bit 62 i)

def recover22 (v : Nat) (p : Bool) : Bool :=
  let x := v / 2 + 32*p.toNat
  let a := chart22 x 0
  let b := chart22 x 1
  let c := chart22 x 2
  let d := chart22 x 3
  let e := chart22 x 4
  let f := chart22 x 5
  bx (bx (bx (bx (!b && !c) (c && e && !d)) (c && f))
      (a && d && f && !b)) (b && e && f)

theorem row22_recovery :
    ∀ (v : Fin 64) (j : Fin 64),
      let d : Int := 129+2*(v.val : Int)
      let h : Int := (j.val : Int)-32
      let a := 4096+h-16*d
      let b := a-8*d
      let c := step b (4*d)
      let e := step c (2*d)
      let f := step e d
      0 <= a → decide (e < 0) = recover22 v.val (decide (f < 0)) := by decide

-- Multiplicative circuit for the 4-input term using one clean product
-- and a dirty triple. Factor identity is independent of the clean line.
theorem four_factor (a b c d : Bool) :
    (a && b) && (c && d) = ((a && b) && c) && d := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

end GVQCC.FamilyC36
#print axioms GVQCC.FamilyC36.first_row_ladder
#print axioms GVQCC.FamilyC36.first_row_truncated
#print axioms GVQCC.FamilyC36.row25_low_identity
#print axioms GVQCC.FamilyC36.virtual_row24
#print axioms GVQCC.FamilyC36.expand_row23
#print axioms GVQCC.FamilyC36.dirty_triple
#print axioms GVQCC.FamilyC36.cx_involutive
#print axioms GVQCC.FamilyC36.row22_recovery
#print axioms GVQCC.FamilyC36.four_factor
