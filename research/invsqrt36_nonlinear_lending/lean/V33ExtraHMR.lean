import Std.Tactic
namespace GVQCC.V33ExtraHMR
def X := Bool.xor

-- Source 30265: h=q6*q14, k=q21*q24, y=q28;
-- L=q35 xor q31 xor q12 xor q7 xor q3 xor q34 xor q11.
-- g=record419, j=record837, m=original HMR event,
-- n=fresh independent HMR event on unused scratch record 1018.
-- Projected state: (h,z,y xor k,phase,scratch).
def old (h k y z l g j m : Bool) : Bool × Bool × Bool × Bool × Bool :=
  (h,z,X y k,X (X (g && y && k) (j && l && k)) (m && k),false)

def new (h k y z l g j m n : Bool) : Bool × Bool × Bool × Bool × Bool :=
  let p := X (m && h) (m && h)
  let p := X p (g && y && k)
  let p := X p (j && l && k)
  let p := X p (m && k)
  let p := X p (n && k)
  let p := X p (n && k)
  (h,z,X y k,p,false)

theorem measured_rank_two_projection (h k y z l g j m n : Bool) :
    old h k y z l g j m = new h k y z l g j m n := by
  cases h <;> cases k <;> cases y <;> cases z <;>
    cases l <;> cases g <;> cases j <;> cases m <;> cases n <;> decide

theorem fresh_measurement_debt (n a b : Bool) :
    X (n && a && b) (n && (a && b)) = false := by
  cases n <;> cases a <;> cases b <;> decide

theorem native_receipt : 3 - 2 = 1 ∧ 26 - 17 = 9 := by decide
end GVQCC.V33ExtraHMR
