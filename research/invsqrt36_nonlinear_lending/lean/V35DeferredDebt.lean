import Std.Tactic
namespace GVQCC.V35
def X := Bool.xor

-- A fresh X-basis measurement contributes a Boolean sign exponent m*f.
-- No initial decoder is required: the recovery premise is at the exit.
theorem delayed_debt (p m f r : Bool) (h : r = f) :
    X (X p (m && f)) (m && r) = p := by
  subst r
  cases p <;> cases m <;> cases f <;> decide

-- The recovery equation is a reachable-state premise, not an assumption
-- that the parked value is a quadratic function of the entry coordinates.
theorem exit_product (p m f a b : Bool) (h : f = (a && b)) :
    X (X p (m && f)) (m && (a && b)) = p := by
  exact delayed_debt p m f (a && b) h.symm

-- Record publication: defer writing the original classical record until
-- its source event. Clearing followed by a conditional XOR copies m.
theorem publish (old m : Bool) :
    (X false m, false) = (m, false) := by
  cases m <;> decide

-- Multiple debts may be discharged in any order. All outcome bits are
-- arbitrary; there is no postselection.
def parity : List Bool → Bool
  | [] => false
  | a :: as => X a (parity as)

theorem parity_append (xs ys : List Bool) :
    parity (xs ++ ys) = X (parity xs) (parity ys) := by
  induction xs with
  | nil =>
    change parity ys = X false (parity ys)
    cases parity ys <;> rfl
  | cons a as ih =>
    change X a (parity (as ++ ys)) = X (X a (parity as)) (parity ys)
    rw [ih]
    cases a <;> cases parity as <;> cases parity ys <;> rfl

def debt (xs : List (Bool × Bool)) : Bool :=
  parity (xs.map (fun q => q.1 && q.2))

theorem settle_all (p : Bool) (xs : List (Bool × Bool)) :
    X (X p (debt xs)) (debt xs) = p := by
  cases p <;> cases debt xs <;> decide

-- A moving representative changes f to f xor d. This gives precisely
-- the transported phase remainder, including measurement coefficients.
theorem transport (m f d : Bool) :
    X (m && f) (m && X f d) = (m && d) := by
  cases m <;> cases f <;> cases d <;> decide

-- An arbitrary length discrete phase integration-by-parts identity.
def edgeSum (c : Bool) : List (Bool × Bool) → Bool
  | [] => false
  | (k,d) :: xs => X (k && X c d) (edgeSum d xs)

def boundary (k c : Bool) : List (Bool × Bool) → Bool
  | [] => k && c
  | (l,d) :: xs => X (X k l && c) (boundary l d xs)

theorem boundary_step (k c l d t : Bool) :
    X (k && c) (X (l && X c d) t) =
      X (X k l && c) (X (l && d) t) := by
  cases k <;> cases c <;> cases l <;> cases d <;> cases t <;> decide

theorem weighted_parts (k c : Bool) (xs : List (Bool × Bool)) :
    X (k && c) (edgeSum c xs) = boundary k c xs := by
  induction xs generalizing k c with
  | nil => cases k <;> cases c <;> decide
  | cons z zs ih =>
    rcases z with ⟨l,d⟩
    change X (k && c) (X (l && X c d) (edgeSum d zs)) =
      X (X k l && c) (boundary l d zs)
    rw [← ih l d]
    exact boundary_step k c l d (edgeSum d zs)

-- Native V27 source [31033,31284), logical q18 unchanged and
-- q18=q8*q29 at exit. The extracted premise is independently checked
-- by BDD. The theorem is a projected phase obligation, not whole KMB.
theorem native31033 (p m q18 q8 q29 : Bool)
    (h : q18 = (q8 && q29)) :
    (q18, p, false) =
      ((q8 && q29), X (X p (m && q18)) (m && (q8 && q29)), false) := by
  subst q18
  cases p <;> cases m <;> cases q8 <;> cases q29 <;> decide

theorem chart_receipts :
    46089 + 308 = 46397 ∧ 5167 - 308 = 4859 ∧
    22501 + 640 = 23141 ∧ 23157 - 16 = 23141 ∧
    1276 + 10 = 1286 ∧ 31284 - 31033 = 251 := by decide

end GVQCC.V35
