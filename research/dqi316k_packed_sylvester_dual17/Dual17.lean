import Init
import Std
namespace GVQCC.Dual17
def xtime (x : Nat) : Nat := if x.testBit 2 then (2*x) ^^^ 11 else 2*x
def mul8 (x y : Nat) : Nat :=
  (if y.testBit 0 then x else 0) ^^^
  (if y.testBit 1 then xtime x else 0) ^^^
  (if y.testBit 2 then xtime (xtime x) else 0)
def dualMul (x y : Nat) : Nat :=
  mul8 (x%8) (y%8) + 8 * (mul8 (x%8) (y/8) ^^^ mul8 (x/8) (y%8))
def form (l x : Nat) : Bool :=
  (List.range 6).foldl (fun a i => Bool.xor a (l.testBit i && x.testBit i)) false
def terms : List (Nat × Nat) :=
  [(2,42),(6,23),(7,33),(40,14),(41,11),(42,3),(43,46),(44,61),(47,21),(49,24),(51,8),(52,40),(53,56),(58,56),(59,48),(61,40),(63,32)]
def tensorMul (x y : Nat) : Nat :=
  terms.foldl (fun a (l,w) => if form l x && form l y then a ^^^ w else a) 0
set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem basis_check :
    (List.range 6).all (fun i => (List.range 6).all (fun j =>
      tensorMul (2^i) (2^j) == dualMul (2^i) (2^j))) = true := by decide
theorem rank_count : terms.length = 17 := by decide
#print axioms basis_check
#print axioms rank_count
end GVQCC.Dual17
