import Std.Tactic
namespace GVQCC.V33

-- Six affine maps fixing (true,true), i.e. the product-one point.
theorem product_stabilizer (u v : Bool) :
    ((u && v) = (v && u)) ∧
    ((u && v) = (u && !(Bool.xor u v))) ∧
    ((u && v) = (!(Bool.xor u v) && u)) ∧
    ((u && v) = (v && !(Bool.xor u v))) ∧
    ((u && v) = (!(Bool.xor u v) && v)) := by
  cases u <;> cases v <;> decide

theorem complement_carry (a b c : Bool) :
    ((Bool.xor a c) && (Bool.xor b c)) =
      ((Bool.xor (!a) (!c)) && (Bool.xor (!b) (!c))) := by
  cases a <;> cases b <;> cases c <;> decide

theorem annihilator_care (a b d : Bool) (h : (a && d) = false) :
    (a && Bool.xor b d) = (a && b) := by
  cases a <;> cases b <;> cases d <;> simp_all

theorem polar_transport (a b da db : Bool) :
    Bool.xor ((Bool.xor a da) && (Bool.xor b db)) (a && b) =
    Bool.xor (Bool.xor (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

theorem projected_reset (a b t l m : Bool)
    (h : Bool.xor t (a && b) = l) :
    (Bool.xor (m && t) (Bool.xor (m && a && b) (m && l)) = false) ∧
    Bool.xor false l = Bool.xor t (a && b) := by
  cases a <;> cases b <;> cases t <;> cases l <;> cases m <;> simp_all

theorem edge_telescopes (a b c : Bool) :
    Bool.xor (Bool.xor a b) (Bool.xor b c) = Bool.xor a c := by
  cases a <;> cases b <;> cases c <;> decide

theorem weighted_edge_adjoint (a b c k l : Bool) :
    Bool.xor (k && Bool.xor a b) (l && Bool.xor b c) =
      Bool.xor (Bool.xor (k && a) (Bool.xor k l && b)) (l && c) := by
  cases a <;> cases b <;> cases c <;> cases k <;> cases l <;> decide

-- Actual native cut 36276: reachability hypothesis certified by BDD.
theorem actual_affine_update (q30 q28 q24 q8 : Bool)
    (h : (q30 && q28) = q24) :
    Bool.xor q8 (q30 && q28) = Bool.xor q8 q24 := by rw [h]

-- Resource bookkeeping of sparse eleven-edit candidate.
theorem resource_certificate :
    77 + 3 = 80 ∧
    23157 - 11 * 16 = 22981 ∧
    1599 - 11 = 1588 ∧
    54095 + 32 = 54127 ∧
    1276 + 10 = 1286 := by decide

end GVQCC.V33
