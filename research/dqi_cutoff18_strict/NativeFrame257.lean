import Mathlib

namespace GVQCC.NativeFrame257

def cx (a b : Bool) : Bool × Bool := (a, Bool.xor a b)
def cy (a b : Bool) : Bool × Bool := (Bool.xor a b, b)
def ccx (c a b : Bool) : Bool × Bool := (Bool.xor a (c && b), b)

theorem three_shears (a b : Bool) :
    let p := cx a b
    let q := cy p.1 p.2
    cx q.1 q.2 = (b,a) := by
  cases a <;> cases b <;> decide

theorem fredkin_shared_frame (c a b : Bool) :
    let p := cx a b
    let q := ccx c p.1 p.2
    cx q.1 q.2 = if c then (b,a) else (a,b) := by
  cases c <;> cases a <;> cases b <;> decide

theorem common_phase (a b c d : Bool) :
    Bool.xor (a && b && c) (a && b && d) =
    (a && b && Bool.xor c d) := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

theorem rank_exchange {R : Type*} [CommRing R] (h2 : (2:R)=0)
    (a b d v w : R) :
    a*b*v+a*d*w=a*(b+d)*v+a*d*(v+w) := by
  calc
    _ = a*b*v+a*d*w+2*a*d*v := by rw [h2]; ring
    _ = _ := by ring

end GVQCC.NativeFrame257

#print axioms GVQCC.NativeFrame257.three_shears
#print axioms GVQCC.NativeFrame257.fredkin_shared_frame
#print axioms GVQCC.NativeFrame257.common_phase
#print axioms GVQCC.NativeFrame257.rank_exchange
