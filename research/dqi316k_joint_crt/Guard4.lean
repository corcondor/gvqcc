import Init
namespace GVQCC.Guard4
def x := Bool.xor
def gated (a b c r : Bool) : Bool × Bool × Bool :=
  (r && x (x (x a b) c) (b && c),
   r && x c (a && b),
   r && x (x b c) (a && c))
def shared (a b c r : Bool) : Bool × Bool × Bool :=
  let g1 := (!c) && (!b)
  let g2 := (!r) && x (!a) g1
  let g3 := x c r && x (x (x a b) g1) g2
  let g4 := x b r && x (x (x (x (!a) c) r) g1) g2
  (x (x (!a) g1) g2,
   x (x (x (x (x a b) c) r) g2) g4,
   x (x (x (x a b) r) g2) g3)

theorem four_products (a b c r : Bool) : shared a b c r = gated a b c r := by
  cases a <;> cases b <;> cases c <;> cases r <;> decide

theorem hmr_erase (p a b m : Bool) :
    x (x p (m && a && b)) (m && (a && b)) = p := by
  cases p <;> cases a <;> cases b <;> cases m <;> decide

theorem affine_coordinate_inverse (p q t : Bool) :
    x (x p (x q t)) (x q t) = p := by
  cases p <;> cases q <;> cases t <;> decide

theorem common_control_fold (a b c t : Bool) :
    x (x t (a && b)) (a && c) = x t (a && x b c) := by
  cases a <;> cases b <;> cases c <;> cases t <;> decide

theorem independent_xor_commute (p q t : Bool) :
    x (x t p) q = x (x t q) p := by
  cases p <;> cases q <;> cases t <;> decide

theorem self_inverse_update (p t : Bool) : x (x t p) p = t := by
  cases p <;> cases t <;> decide
end GVQCC.Guard4
#print axioms GVQCC.Guard4.four_products
#print axioms GVQCC.Guard4.hmr_erase
#print axioms GVQCC.Guard4.affine_coordinate_inverse
#print axioms GVQCC.Guard4.common_control_fold
#print axioms GVQCC.Guard4.independent_xor_commute
#print axioms GVQCC.Guard4.self_inverse_update
