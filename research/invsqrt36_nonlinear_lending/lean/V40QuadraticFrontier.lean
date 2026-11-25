import Std.Tactic
namespace GVQCC.V40

def parity : List Bool → Bool
  | [] => false
  | a :: xs => Bool.xor a (parity xs)

-- The common alternating rank-two matrix is a product of two affine factors.
theorem rectangle (a b c d : Bool) :
    parity [a && c,a && d,b && c,b && d] =
      (Bool.xor a b && Bool.xor c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

-- These factor forms are universal. Their applicability to the actual
-- observation frontier is a reachable premise proved by packed truth tables.
theorem frontier633 (f14 f16 f20 f34 : Bool) :
    parity [f14 && f20,f14 && f34,f16 && f20,f16 && f34] =
      (Bool.xor f14 f16 && Bool.xor f20 f34) :=
  rectangle f14 f16 f20 f34

theorem frontier454 (f14 f34 f16 f20 : Bool) :
    parity [f14 && f16,f14 && f20,f34 && f16,f34 && f20] =
      (Bool.xor f14 f34 && Bool.xor f16 f20) :=
  rectangle f14 f34 f16 f20

-- The projection is injective on the graph of a decoder, not on all states.
theorem graph_projection_injective {α : Type} (f : α → Bool)
    (x y : α) (a b : Bool) (ha : a = f x) (hb : b = f y)
    (h : x = y) : (x,a) = (y,b) := by
  subst y
  rw [ha,hb]

-- Erase a measured quadratic coordinate using a classical sign correction.
theorem quadratic_sign (q a b l m : Bool)
    (h : q = Bool.xor (a && b) l) :
    parity [m && q,m && a && b,m && l] = false := by
  rw [h]
  cases a <;> cases b <;> cases l <;> cases m <;> decide

-- If a retained coordinate undergoes a sequence of XOR updates, phase
-- differences telescope independently of the intermediate representations.
def updates : Bool → List Bool → Bool
  | q, [] => q
  | q, d :: ds => updates (Bool.xor q d) ds

theorem telescope (q : Bool) (ds : List Bool) :
    updates q ds = Bool.xor q (parity ds) := by
  induction ds generalizing q with
  | nil => cases q <;> rfl
  | cons d ds ih =>
    change updates (Bool.xor q d) ds =
      Bool.xor q (Bool.xor d (parity ds))
    rw [ih]
    cases q <;> cases d <;> cases parity ds <;> rfl

theorem phase_boundary (m q : Bool) (ds : List Bool) :
    Bool.xor (m && q) (m && updates q ds) = (m && parity ds) := by
  rw [telescope]
  cases m <;> cases q <;> cases parity ds <;> rfl

theorem resource_counts :
    23127 - 2 * 16 = 23095 ∧
    3239 - 90 = 3149 ∧ 3239 - 110 = 3129 ∧
    23095 + 8 * 16 = 23223 ∧
    704 - 680 = 24 ∧ 8 + 5 = 13 ∧
    41935 + 10 + 5 = 41950 := by decide

end GVQCC.V40
