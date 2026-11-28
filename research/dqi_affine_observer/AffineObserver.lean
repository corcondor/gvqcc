import Std
namespace GVQCC.AffineObserver

def bx (a b : Bool) : Bool := Bool.xor a b
def df (x p d : Bool) : Bool := bx x (p && d)

theorem cx_transport (x y p dx dy : Bool) :
    bx (df y p dy) (df x p dx) = df (bx y x) p (bx dy dx) := by
  cases x <;> cases y <;> cases p <;> cases dx <;> cases dy <;> decide

theorem x_transport (x p d : Bool) :
    ! (df x p d) = df (!x) p d := by
  cases x <;> cases p <;> cases d <;> decide

theorem linear_observer (x p d : Bool) :
    bx (df x p d) x = (p && d) := by
  cases x <;> cases p <;> cases d <;> decide

theorem quadratic_observer (x y p d e : Bool) :
    bx (df x p d && df y p e) (x && y) =
      (p && bx (bx (d && y) (e && x)) (d && e)) := by
  cases x <;> cases y <;> cases p <;> cases d <;> cases e <;> decide

theorem cubic_observer (x y z p a b c : Bool) :
    bx (df x p a && df y p b && df z p c) (x && y && z) =
      (p && bx (bx (bx (a && y && z) (b && x && z)) (c && x && y))
              (bx (bx (a && b && z) (a && c && y)) (bx (b && c && x) (a && b && c)))) := by
  cases x <;> cases y <;> cases z <;> cases p <;> cases a <;> cases b <;> cases c <;> decide

theorem hmr_debt (x p d m : Bool) :
    bx (m && df x p d) (m && x) = (m && p && d) := by
  cases x <;> cases p <;> cases d <;> cases m <;> decide

theorem carry_phase (old debt correction : Bool) (h : correction = debt) :
    bx (bx old debt) correction = old := by
  subst correction
  cases old <;> cases debt <;> decide

theorem equal_product_closes (x p : Bool) :
    bx (df x p true) p = x := by
  cases x <;> cases p <;> decide

theorem two_observations (x y p m n : Bool) :
    bx (m && bx x p) (n && bx y p) =
      bx (bx (m && x) (n && y)) (p && bx m n) := by
  cases x <;> cases y <;> cases p <;> cases m <;> cases n <;> decide

#print axioms cx_transport
#print axioms x_transport
#print axioms linear_observer
#print axioms quadratic_observer
#print axioms cubic_observer
#print axioms hmr_debt
#print axioms carry_phase
#print axioms equal_product_closes
#print axioms two_observations
end GVQCC.AffineObserver
