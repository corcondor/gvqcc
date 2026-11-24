import Std.Tactic
namespace GVQCC.V36

-- Actual decoder at native PR86 cut 7430 (PR89 economy cut 7429).
def decoder (x y z w : Bool) : Bool :=
  Bool.xor (Bool.xor x y)
    (Bool.xor (Bool.xor (x && y) (x && z))
      (Bool.xor (x && w) (Bool.xor (y && z) (z && w))))

theorem rank_one_decoder (x y z w : Bool) :
    decoder x y z w =
      Bool.xor ((Bool.xor x z) && (Bool.xor (Bool.xor y z) w))
        (Bool.xor (Bool.xor x y) z) := by
  cases x <;> cases y <;> cases z <;> cases w <;> decide

theorem care_cofactor (b c r : Bool)
    (h : (b && Bool.xor c r) = false) :
    (b && c) = (b && r) := by
  cases b <;> cases c <;> cases r <;> (first | decide | contradiction)

theorem exchange_mux (a b c : Bool) :
    Bool.xor c (a && b) =
      Bool.xor ((Bool.xor a c) && b) (c && !b) := by
  cases a <;> cases b <;> cases c <;> decide

-- CNOT sandwich around one computation of a shared product.
theorem fanout (u v x y : Bool) :
    let f := u && v
    let y0 := Bool.xor y x
    let x1 := Bool.xor x f
    (x1, Bool.xor y0 x1) = (Bool.xor x f, Bool.xor y f) := by
  cases u <;> cases v <;> cases x <;> cases y <;> decide

-- Erase-and-recompute vs retain the old carrier and update it in place.
-- c = R is a reachable-state premise independently certified by BDD.
theorem inplace_carry (a b c r : Bool) (h : c = r) :
    (Bool.xor a c, Bool.xor c (a && b)) =
      (Bool.xor a r, Bool.xor c (a && b)) := by rw [h]

theorem measured_decoder_sign (x y z w c m : Bool)
    (h : c = decoder x y z w) :
    Bool.xor (m && c) (m && decoder x y z w) = false := by
  rw [h]
  cases m <;> cases decoder x y z w <;> decide

-- Change the omitted coordinate p -> q without making a second live copy.
theorem pivot_exchange (p q r : Bool)
    (h : r = Bool.xor p q) :
    Bool.xor q r = p := by
  rw [h]; cases p <;> cases q <;> decide

-- Carry derivative / GF(2) summation by parts for an arbitrary chain.
def edges (c : Bool) : List Bool → List Bool
  | [] => []
  | d :: ds => Bool.xor c d :: edges d ds

def xorList : List Bool → Bool
  | [] => false
  | d :: ds => Bool.xor d (xorList ds)

def endpoint (c : Bool) : List Bool → Bool
  | [] => c
  | d :: ds => endpoint d ds

theorem telescoping (c : Bool) (ds : List Bool) :
    xorList (edges c ds) = Bool.xor c (endpoint c ds) := by
  induction ds generalizing c with
  | nil => cases c <;> rfl
  | cons d ds ih =>
    change Bool.xor (Bool.xor c d) (xorList (edges d ds)) =
      Bool.xor c (endpoint d ds)
    rw [ih]
    cases h : endpoint d ds <;> cases c <;> cases d <;> rfl

theorem weighted_two_edges (a b c k l : Bool) :
    Bool.xor (k && Bool.xor a b) (l && Bool.xor b c) =
      Bool.xor (Bool.xor (k && a) (Bool.xor k l && b)) (l && c) := by
  cases a <;> cases b <;> cases c <;> cases k <;> cases l <;> decide

theorem audit_counts :
    22 + 2 = 24 ∧ 130 ≤ 161 ∧ 3702 - 9 * 3 = 3675 ∧
    23077 + 9 * 16 = 23221 := by decide
end GVQCC.V36
