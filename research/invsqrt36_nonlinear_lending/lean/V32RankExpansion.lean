import Std.Tactic
namespace GVQCC.V32
def X := Bool.xor

-- Rank-two generator-frame shear: the primal and dual transforms cancel.
theorem rank_two_frame (f h u v : Bool) :
    X (u && f) (v && h) = X (u && X f h) (X u v && h) := by
  cases f <;> cases h <;> cases u <;> cases v <;> decide

-- For two distinct product generators the four temporal boundary terms
-- collapse to their common observation applied to the joint delta.
theorem temporal_pair (x y h k g : Bool) :
    X (g && x && y) (g && X (X x h) k && y) =
      (g && X h k && y) := by
  cases x <;> cases y <;> cases h <;> cases k <;> cases g <;> decide

-- Unlike the linear pair, an observation of two changing coordinates
-- needs the cross term (quadratic remainder).
theorem two_coordinate_observation (x y h k g : Bool) :
    X (g && x && y) (g && X x h && X y k) =
      (g && X (X (x && k) (y && h)) (h && k)) := by
  cases x <;> cases y <;> cases h <;> cases k <;> cases g <;> decide

-- Actual mapped V31 bridge 30265..30278.
-- h=q6*q14, k=q21*q24, y=q28, z=physical q25.
-- l is the XOR of q35,q31,q12,q7,q3,q34,q11.
-- g=record419, j=record837, m=the existing HMR outcome (record1).
-- Entry premise physical q33=h established by full-domain BDD.
-- Original computes clear(h), k, HMR(k), recompute(h).
-- Candidate omits clear(h), transfers the data delta to q28 at exit and
-- pays three phase debts on the same original records.
def old (h k y z l g j m : Bool) : Bool × Bool × Bool × Bool :=
  (h,z,X y k,X (X (g && y && k) (j && l && k)) (m && k))

def new (h k y z l g j m : Bool) : Bool × Bool × Bool × Bool :=
  let v := X h k
  let p := X (g && y && h) (g && y && v)
  let p := X p (j && l && v)
  let p := X p (m && v)
  let p := X p (j && l && h)
  let p := X p (m && h)
  (h,z,X (X y v) h,p)

theorem native30265_projection (h k y z l g j m : Bool) :
    old h k y z l g j m = new h k y z l g j m := by
  cases h <;> cases k <;> cases y <;> cases z <;>
  cases l <;> cases g <;> cases j <;> cases m <;> decide

theorem native30265_guarded (a b k y z l g j m t : Bool)
    (ht : t = (a && b)) :
    old (a && b) k y z l g j m = new t k y z l g j m := by
  subst t
  exact native30265_projection (a && b) k y z l g j m

-- Each non-linear update changes one coordinate by a single function.
-- This is the generator inclusion used by the span-rank bound, not a
-- formal proof of all finite-dimensional linear-algebra lemmas.
def coordUpdate (s : Nat → Bool) (p : Nat) (h : Bool) : Nat → Bool :=
  fun i => if i = p then X (s i) h else s i

theorem single_generator_update (s : Nat → Bool) (p : Nat) (h : Bool) (i : Nat) :
    coordUpdate s p h i = X (s i) ((decide (i = p)) && h) := by
  by_cases hi : i = p
  · simp [coordUpdate, hi, X]
  · simp [coordUpdate, hi, X]

theorem exact_rank_receipts :
    39 - 37 = 2 ∧ 39 - 36 = 3 ∧
    38 - 37 = 1 ∧ 38 - 36 = 2 := by decide
theorem native_cost_receipt :
    3 - 2 = 1 ∧ 57 - 26 = 31 ∧ 45975 + 13 = 45988 := by decide
end GVQCC.V32
