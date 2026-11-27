import Init

/-! V122: reversible quotient-bit reconstruction and a bounded cross-row
recoverability certificate. Local Boolean/arithmetic statements only. -/
namespace GVQCC.FamilyCV122
set_option maxRecDepth 100000
set_option maxHeartbeats 0

def bx (a b : Bool) : Bool := Bool.xor a b

def row23 (a b c d p : Bool) : Bool :=
  let g := (bx (bx a b) c) && bx d p
  bx (bx b g) (bx c g && bx b p)

/-- The nonlinear factor can be temporarily stored in a dirty source
coordinate, without any additional clean qubit. Arbitrary target z. -/
theorem row23_shear (a b c d p z : Bool) :
    let l := bx (bx a b) c
    let r := bx d p
    let c1 := bx c (l && r)
    let z1 := bx (bx (bx (bx z b) c) c1) (c1 && bx b p)
    let c2 := bx c1 (l && r)
    (bx (bx l b) c2, c2, bx r p, z1) = (a,c,d,bx z (row23 a b c d p)) := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases p <;> cases z <;> decide

def row22 (a b u d e f : Bool) : Bool :=
  bx (bx (bx (bx ((!b) && !u) (u && e && !d)) (u && f))
    (a && d && f && !b)) (b && e && f)

/-- Two sequential factored kernels share one temporary. The second
uses a reversible shear to implement the conditional selection; no
non-injective overwrite of the source e is allowed. -/
theorem row22_mux (a b u d e f z : Bool) :
    let t0 := e && !d
    let t1 := bx (bx t0 (!b)) f
    let z1 := bx (bx z (!b)) (u && t1)
    let t2 := a && d
    let e1 := bx e t2
    let t3 := bx t2 (b && e1)
    let z2 := bx z1 (f && t3)
    let t4 := bx t3 (b && e1)
    (bx e1 t4, t4, z2) = (e, a && d, bx z (row22 a b u d e f)) := by
  cases a <;> cases b <;> cases u <;> cases d <;> cases e <;> cases f <;> cases z <;> decide

/-- The first temporary is restored before X-measurement. -/
theorem first_temp_restore (e d b f : Bool) :
    bx (bx (bx (bx (e && !d) (!b)) f) f) (!b) = e && !d := by
  cases e <;> cases d <;> cases b <;> cases f <;> decide

theorem hmr_product (a b t m : Bool) (h : t = a && b) :
    bx (m && t) (m && (a && b)) = false := by
  subst t
  cases a <;> cases b <;> cases m <;> decide

def divWord (v : Int) := 129+2*v
def upd (r d : Int) := if r < 0 then r+d else r-d
def r26 (v h : Int) := 8192+h-32*divWord v
def r25 (v h : Int) := r26 v h - 16*divWord v
def r24 (v h : Int) := upd (r25 v h) (8*divWord v)
def r23 (v h : Int) := upd (r24 v h) (4*divWord v)
def r22 (v h : Int) := upd (r23 v h) (2*divWord v)
def r21 (v h : Int) := upd (r22 v h) (divWord v)

-- Table index is 2*v + [post-row21 remainder < 0].
def care : Nat := 228417890584967033705471397214694604797
def table : Nat := 228403949913572763782473116296913015504

/-- Exact recoverability on the bounded arithmetic chart, not a physical
implementation of row21 retirement or a theorem for arbitrary inputs. -/
theorem row21_table :
    ∀ v : Fin 64, ∀ h : Fin 128,
      let vv : Int := v.val
      let hh : Int := (h.val : Int)-64
      let idx := 2*v.val + (if r21 vv hh < 0 then 1 else 0)
      0 ≤ r26 vv hh →
        care.testBit idx = true ∧
        table.testBit idx = decide (r22 vv hh < 0) := by decide

end GVQCC.FamilyCV122

#print axioms GVQCC.FamilyCV122.row23_shear
#print axioms GVQCC.FamilyCV122.row22_mux
#print axioms GVQCC.FamilyCV122.first_temp_restore
#print axioms GVQCC.FamilyCV122.hmr_product
#print axioms GVQCC.FamilyCV122.row21_table
