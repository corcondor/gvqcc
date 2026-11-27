import Init

/-! Bounded arithmetic and Boolean certificates for compressed MAIN, m=6.
These do not prove the complete physical circuit, HO, or END.
-/
namespace GVQCC.FamilyCCompressed36
set_option maxRecDepth 100000
set_option maxHeartbeats 0

def bx (a b : Bool) : Bool := Bool.xor a b
def bit (x : Int) (i : Nat) : Bool := decide (x / (2^i : Int) % 2 = 1)
def zval (v h : Int) := 250+h-12*v
def dval (v : Int) := 129+2*v
def update (z d : Int) := if z < 0 then z+d else z-d

def pre (v z : Int) : Bool :=
  let a := bx (bit v 3) (bit v 5)
  let b := bx (bit z 7) (bit v 5)
  bx (bit v 5) (bit v 4 && bx (bx (bx (bit v 5) a) b) (a && b))

def post (v w : Int) : Bool :=
  let a := bit v 3
  let b := bit v 4
  let c := bit w 6
  let d := bit w 7
  bx (bx (bx (bx (bit v 5) a) b) (a && b))
    (bx (bx a b) c && bx (bx a b) d)

/-- 1024 local inputs, guard at row 26. Exact finite proof by kernel reduction. -/
theorem top_local :
    ∀ v : Fin 64, ∀ h : Fin 16,
      let vv : Int := v.val
      let hh : Int := (h.val : Int)-8
      let z := zval vv hh
      let w := update z (dval vv)
      0 ≤ z+2*dval vv →
        pre vv z = decide (z < 0) ∧
        bx (pre vv z) (post vv w) = decide (w < 0) ∧
        -256 ≤ w ∧ w < 256 := by decide

theorem post_factor (a b c d : Bool) :
    bx (bx (bx a b) (a && b)) (bx (bx a b) c && bx (bx a b) d) =
      bx (bx (bx (bx (bx (a && b) (a && c)) (a && d)) (b && c)) (b && d)) (c && d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

def r26 (v h : Int) := 8192+h-32*dval v
def r25 (v h : Int) := r26 v h - 16*dval v
def r24 (v h : Int) := update (r25 v h) (8*dval v)
def r23 (v h : Int) := update (r24 v h) (4*dval v)
def r22 (v h : Int) := update (r23 v h) (2*dval v)

def cube (x : Nat) (t : Nat × Nat) : Bool := decide ((x &&& t.1) = t.2)
def evalESOP (x : Nat) (ts : List (Nat × Nat)) : Bool :=
  ts.foldl (fun acc t => bx acc (cube x t)) false

def terms23 : List (Nat × Nat) :=
  [(16,16),(32,32),(41,1),(49,32),(73,72),(80,64),(97,97),(104,72)]
def terms22 : List (Nat × Nat) :=
  [(0,0),(8,8),(9,8),(24,16),(32,32),(37,1),(48,16),(57,9),
   (60,24),(80,16),(81,65),(88,0),(96,64),(112,96),(116,64)]

def index (v : Nat) (p : Bool) := 2*v + if p then 1 else 0

/-- 8192 arithmetic cases, with initial nonnegative remainder guard.
h = floor(U/2^14), represented by h.val-64. -/
theorem retire_local :
    ∀ v : Fin 64, ∀ h : Fin 128,
      let vv : Int := v.val
      let hh : Int := (h.val : Int)-64
      0 ≤ r26 vv hh →
        evalESOP (index v.val (decide (r23 vv hh < 0))) terms23 =
          decide (r24 vv hh < 0) ∧
        evalESOP (index v.val (decide (r22 vv hh < 0))) terms22 =
          decide (r23 vv hh < 0) := by decide

/-- For every lower word, the sign is determined by the scaled quotient. -/
theorem sign_scale (a r : Int) (hr : 0 ≤ r) (hu : r < 2097152) :
    a*2097152+r < 0 ↔ a < 0 := by omega

/-- Preserve the fixed low remainder as an exact invariant across a row. -/
theorem update_scale (a r d : Int) (hr : 0 ≤ r) (hu : r < 2097152) :
    update (a*2097152+r) (d*2097152) =
      (update a d)*2097152+r := by
  unfold update
  by_cases ha : a < 0
  · have hh := (sign_scale a r hr hu).2 ha
    simp only [if_pos ha, if_pos hh]
    omega
  · have hh : ¬ a*2097152+r < 0 := fun h => ha ((sign_scale a r hr hu).1 h)
    simp only [if_neg ha, if_neg hh]
    omega

/-- Delayed phase payment uses the same logical value, not its stale wire. -/
theorem deferred_hmr (m s f : Bool) (hs : f=s) :
    bx (m && s) (m && f) = false := by
  subst f
  cases m <;> cases s <;> decide

/-- Dirty borrowed ancilla MCX for three controls; both values restored. -/
theorem dirty_triple (a b c q t : Bool) :
    let q1 := bx q (a && b)
    let t1 := bx t (q1 && c)
    let q2 := bx q1 (a && b)
    (q2, bx t1 (q2 && c)) = (q, bx t (a && b && c)) := by
  cases a <;> cases b <;> cases c <;> cases q <;> cases t <;> decide

end GVQCC.FamilyCCompressed36
#print axioms GVQCC.FamilyCCompressed36.top_local
#print axioms GVQCC.FamilyCCompressed36.post_factor
#print axioms GVQCC.FamilyCCompressed36.retire_local
#print axioms GVQCC.FamilyCCompressed36.sign_scale
#print axioms GVQCC.FamilyCCompressed36.update_scale
#print axioms GVQCC.FamilyCCompressed36.deferred_hmr
#print axioms GVQCC.FamilyCCompressed36.dirty_triple
