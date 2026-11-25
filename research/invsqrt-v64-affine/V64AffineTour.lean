import Std.Tactic
namespace GVQCC.V64AffineTour
def bx (a b : Bool) := Bool.xor a b
theorem quadratic_delta (a b da db : Bool) :
    bx (bx a da && bx b db) (a && b) =
      bx (bx (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide
theorem abel (m n a b : Bool) :
    bx (m && a) (n && b) = bx (bx m n && a) (n && bx a b) := by
  cases m <;> cases n <;> cases a <;> cases b <;> decide
theorem quotient_rounding (p : Int) :
    (p+4)/8 - (p%8)/4 = p/8 := by omega
theorem affine_edge (a b za zb ca cb y : Int)
    (ha : a*za+ca=y) (hb : b*zb+cb=y) :
    b*zb=a*za+ca-cb := by omega
theorem inverse3 : (3*171 : Nat)%512=1 := by decide
theorem inverse5 : (5*205 : Nat)%512=1 := by decide
theorem inverse13 : (13*197 : Nat)%512=1 := by decide
theorem exclusive_sum (a b : Bool) (h : (a && b) = false) :
    (if a then (1 : Nat) else 0) + (if b then 1 else 0) =
      (if bx a b then 1 else 0) := by
  cases a <;> cases b <;> decide
theorem retained_count : (List.range 17).foldl (fun s i => s + ((List.range 13).filter (fun j => decide (11 ≤ i+j))).length) 0 = 155 := by decide
end GVQCC.V64AffineTour
