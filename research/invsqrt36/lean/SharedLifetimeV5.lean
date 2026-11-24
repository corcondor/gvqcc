import Init
set_option maxRecDepth 8192
set_option maxHeartbeats 2000000
/-! V5 algebraic and concrete coefficient certificates.
The reachability hypotheses, KMB instruction semantics, and global phase ledger
are checked separately by the exact symbolic trace; this is not a full
quantum-channel theorem. -/
namespace GVQCC.SharedLifetimeV5
def bx (a b : Bool) : Bool := Bool.xor a b

theorem fresh_measurement_cancel (p y decoder m : Bool) (h : y = decoder) :
    bx (bx p (y && m)) (decoder && m) = p := by
  subst y
  cases p <;> cases decoder <;> cases m <;> decide

theorem write_only_pair (t a b : Bool) :
    bx (bx t a) b = bx t (bx a b) := by
  cases t <;> cases a <;> cases b <;> decide

theorem zero_phase_coefficient (p m : Bool) :
    bx p (m && false) = p := by
  cases p <;> cases m <;> decide

-- Canonical square-free monomials, with x*x=x. Coefficients in GF(2).
def mono (a b : Nat) : List Nat :=
  if a = b then [a] else [min a b, max a b]
def toggle (xs : List (List Nat)) (x : List Nat) : List (List Nat) :=
  if xs.contains x then xs.erase x else x :: xs
def normal (xs : List (List Nat)) : List (List Nat) :=
  xs.foldl toggle []
def expand (ps : List (List Nat × List Nat)) (aff : List (List Nat)) :
    List (List Nat) :=
  normal (aff ++ ps.flatMap (fun p => p.1.flatMap (fun a => p.2.map (mono a))))
def same (a b : List (List Nat)) : Bool :=
  a.all (fun x => b.contains x) && b.all (fun x => a.contains x)

def p25 : List (List Nat × List Nat) :=
  [([2],[15]),([5,6,35],[29]),([6,23],[11,18,22,23]),
   ([7,13],[26,27]),([13,23,35],[18,19,22,27,28]),
   ([16,19,22,27,28],[35]),([19,28,34],[22,23]),([23,34],[27,34])]
def a25 : List (List Nat) := [[13],[18],[19],[28],[29],[34]]
def e25 : List (List Nat) :=
  [[13],[18],[19],[23],[28],[29],[2,15],[5,29],[6,11],[6,18],
   [6,22],[6,23],[6,29],[7,26],[7,27],[11,23],[13,18],[13,19],
   [13,22],[13,26],[13,28],[16,35],[18,35],[19,22],[22,28],
   [22,34],[27,34],[29,35]]

def p29 : List (List Nat × List Nat) :=
  [([2],[6]),([7,8],[10,11,13,14,19,22,25,27]),([8,22],[11,22,27,34]),
   ([16,18,20],[35]),([22,34],[27,34])]
def a29 : List (List Nat) :=
  [[2],[6],[10],[11],[13],[14],[15],[19],[20],[22],[25],[34]]
def e29 : List (List Nat) :=
  [[2],[6],[10],[11],[13],[14],[15],[19],[20],[25],[2,6],[7,10],
   [7,11],[7,13],[7,14],[7,19],[7,22],[7,25],[7,27],[8,10],
   [8,13],[8,14],[8,19],[8,25],[8,34],[11,22],[16,35],[18,35],
   [20,35],[27,34]]

theorem q25_factor_coefficients : same (expand p25 a25) (normal e25) = true := by decide
theorem q29_factor_coefficients : same (expand p29 a29) (normal e29) = true := by decide
theorem paid_factor_count : p25.length + p29.length = 13 := by decide

end GVQCC.SharedLifetimeV5
