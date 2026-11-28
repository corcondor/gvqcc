import Std
namespace GVQCC.PolarRank
def x (a b : Bool) := Bool.xor a b
def minor (ai aj bi bj : Bool) := x (ai && bj) (aj && bi)
theorem plucker (a b c d e f g h : Bool) :
    x (x (minor a b e f && minor c d g h)
         (minor a c e g && minor b d f h))
       (minor a d e h && minor b c f g) = false := by
  cases a <;> cases b <;> cases c <;> cases d <;>
    cases e <;> cases f <;> cases g <;> cases h <;> decide

def quads : List (Nat × Nat × Nat × Nat × Nat × Nat) :=
  [(0,9,1,6,2,5),(0,10,1,7,3,5),(0,11,1,8,4,5),
   (0,12,2,7,3,6),(0,13,2,8,4,6),(0,14,3,8,4,7),
   (1,12,2,10,3,9),(1,13,2,11,4,9),(1,14,3,11,4,10),
   (2,14,3,13,4,12),(5,12,6,10,7,9),(5,13,6,11,8,9),
   (5,14,7,11,8,10),(6,14,7,13,8,12),(9,14,10,13,11,12)]
def bad (p : Nat) : Bool :=
  quads.any (fun (i,j,k,l,m,n) =>
    x (x (p.testBit i && p.testBit j) (p.testBit k && p.testBit l))
      (p.testBit m && p.testBit n))
def span (gs : List Nat) : List Nat :=
  gs.foldl (fun s v => s ++ s.map (fun w => Nat.xor v w)) [0]
def W70 := span [462,513,11506,16385]
def W84 := span [99,513,6324,11544,16385]
theorem W70_card : W70.length = 16 := by decide
theorem W84_card : W84.length = 32 := by decide
theorem W70_no_repeated : W70.Nodup := by decide
theorem W84_no_repeated : W84.Nodup := by decide
theorem W70_obstruction : W70.all (fun p => p == 0 || bad p) = true := by decide
theorem W84_obstruction : W84.all (fun p => p == 0 || bad p) = true := by decide
end GVQCC.PolarRank
#print axioms GVQCC.PolarRank.plucker
#print axioms GVQCC.PolarRank.W70_card
#print axioms GVQCC.PolarRank.W84_card
#print axioms GVQCC.PolarRank.W70_no_repeated
#print axioms GVQCC.PolarRank.W84_no_repeated
#print axioms GVQCC.PolarRank.W70_obstruction
#print axioms GVQCC.PolarRank.W84_obstruction
