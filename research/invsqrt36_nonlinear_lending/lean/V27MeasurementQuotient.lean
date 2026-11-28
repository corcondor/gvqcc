import Std.Tactic
namespace GVQCC.V27

def parity : List Bool → Bool
  | [] => false
  | a :: as => Bool.xor a (parity as)

theorem guarded_xor (m a b : Bool) :
    (m && Bool.xor a b) = Bool.xor (m && a) (m && b) := by
  cases m <;> cases a <;> cases b <;> decide

theorem guarded_parity (m : Bool) (ds : List Bool) :
    parity (ds.map (fun d => m && d)) = (m && parity ds) := by
  induction ds with
  | nil => cases m <;> rfl
  | cons a ds ih =>
    change Bool.xor (m && a) (parity (ds.map (fun d => m && d))) =
      (m && Bool.xor a (parity ds))
    rw [ih, guarded_xor]

-- Transport of the very same HMR event through a tail of XOR writes.
-- The Boolean denotes the branch phase exponent, not a measured data bit.
theorem existing_hmr_transport (f m : Bool) (ds : List Bool) :
    Bool.xor (m && f) (parity (ds.map (fun d => m && d))) =
      (m && Bool.xor f (parity ds)) := by
  rw [guarded_parity, guarded_xor]

-- Interval MBU: if the original unitary cleanup ends at zero, so does the
-- phase debt. No requirement that the individual write masks be independent.
theorem interval_mbu (f m : Bool) (ds : List Bool)
    (h : Bool.xor f (parity ds) = false) :
    Bool.xor (m && f) (parity (ds.map (fun d => m && d))) = false := by
  rw [existing_hmr_transport, h]
  cases m <;> decide

-- A CNOT controlled by an omitted coordinate is a frame change, not a
-- data write on the quotient. The physical target is unchanged.
theorem virtual_cx (f d v : Bool) :
    Bool.xor (Bool.xor (Bool.xor d (v && f)) f) ((!v) && f) = d := by
  cases f <;> cases d <;> cases v <;> decide

-- A write to the omitted coordinate propagates to the retained quotient.
theorem virtual_target_write (f d v h : Bool) :
    Bool.xor (Bool.xor d (v && f)) (v && Bool.xor f h) =
      Bool.xor d (v && h) := by
  cases f <;> cases d <;> cases v <;> cases h <;> decide

def put (s : Nat → Bool) (i : Nat) (a : Bool) : Nat → Bool :=
  fun j => if j = i then a else s j

theorem write_frame (s t : Nat → Bool) (σ : Nat → Nat)
    (hinj : ∀ x y, σ x = σ y → x = y)
    (h : ∀ i, s i = t (σ i)) (i : Nat) (a : Bool) :
    ∀ j, put s i a j = put t (σ i) a (σ j) := by
  intro j
  by_cases hj : j = i
  · subst j
    simp [put]
  · have hσ : σ j ≠ σ i := fun e => hj (hinj j i e)
    simp [put, hj, hσ, h j]

def swapIndex (i j x : Nat) : Nat :=
  if x = i then j else if x = j then i else x

theorem virtual_swap (s t : Nat → Bool) (σ : Nat → Nat)
    (h : ∀ x, s x = t (σ x)) (i j x : Nat) :
    s (swapIndex i j x) = t (σ (swapIndex i j x)) :=
  h (swapIndex i j x)

-- Two observations with one captured classical guard.
theorem guard_snapshot_pair (g a b : Bool) :
    (g && Bool.xor a b) = Bool.xor (g && a) (g && b) :=
  guarded_xor g a b

theorem lazy_resource_receipt : 56734 - 3339 + 21 = 53416 := by decide
theorem lazy_saving_receipt : 56734 - 53416 = 3318 := by decide
end GVQCC.V27
