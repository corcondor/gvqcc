import Mathlib
namespace GVQCC.MeasuredDual
open scoped BigOperators

/-- Contract the already classical measured output before computing guarded products.
No invertibility, nonzero scalar, or pivot assumption is needed for this identity. -/
theorem measured_contract {R I J K : Type*} [CommSemiring R]
    [Fintype I] [Fintype J] [Fintype K]
    (T : I → J → K → R) (g : R) (x : I → R) (y : J → R) (m : K → R) :
    g * (∑ k, m k * (∑ i, ∑ j, (x i*y j)*T i j k)) =
      ∑ i, ∑ j, (g*x i)*y j*(∑ k,m k*T i j k) := by
  simp only [Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro i _
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro k _
  ring

theorem guarded_debt_cancel (g x m : Bool) :
    Bool.xor (m && (g && x)) (g && x && m) = false := by
  cases g <;> cases x <;> cases m <;> decide

theorem guarded_cache_zero (x : Bool) : (false && x) = false := by rfl

/-- Toggling a parity by the coefficient delta changes it to the new parity. -/
theorem parity_transition (old new : Bool) :
    Bool.xor old (Bool.xor old new) = new := by
  cases old <;> cases new <;> decide

abbrev Term := Nat × Nat × Nat
def original : List Term :=
  [(48,48,3115),(160,160,2936),(2088,2088,1070),(2184,2184,2791),
   (272,272,2801),(321,321,1468),(81,81,3917),(592,592,879),
   (1776,1776,535),(2016,2016,3418),(1697,1697,1963),(608,608,1629),
   (3056,3056,415),(2896,2896,3785),(984,984,1457),(393,393,874),
   (1636,1636,382),(714,714,1033),(119,119,1891),(701,701,2106),
   (820,820,2896),(510,510,3123),(723,723,1869),(3855,3855,2329),
   (3439,3439,1330),(3726,3726,1587),(2282,2282,1283),(2617,2617,590),
   (3165,3165,1149),(2286,2286,2546),(3879,3879,2843),(1947,1947,3615),
   (4027,4027,745),(1877,1877,2042),(156,156,3592),(2162,2162,3297),
   (233,233,1984),(1906,1906,1628),(3943,3943,412),(2300,2300,3971),
   (3982,3982,2115),(3423,3423,2678)]

def gfStep (a : Nat) : Nat :=
  let v := 2*a
  if v.testBit 12 then Nat.xor v 0x1053 else v

def mulLoop : Nat → Nat → Nat → Nat
  | 0, _, _ => 0
  | n+1, a, b => Nat.xor (if b.testBit 0 then a else 0) (mulLoop n (gfStep a) (b/2))

def basisProduct (i j : Nat) : Nat :=
  original.foldl (fun s t => if t.1.testBit i && t.2.1.testBit j then Nat.xor s t.2.2 else s) 0

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem exact_basis :
    (List.range 12).all (fun i => (List.range 12).all
      (fun j => basisProduct i j == mulLoop 12 (2^i) (2^j))) = true := by decide

theorem old_cost : (21-12 : Nat) * 62 = 558 := by decide
theorem new_converter : (183642 - 558 : Nat) = 183084 := by decide
theorem full_prefix : (102066 + 183084 : Nat) = 285150 := by decide
theorem direct_shell_budget : (219629 + 183084 : Nat) > 318344 := by decide

#print axioms measured_contract
#print axioms guarded_debt_cancel
#print axioms guarded_cache_zero
#print axioms parity_transition
#print axioms exact_basis
#print axioms old_cost
#print axioms new_converter
#print axioms full_prefix
#print axioms direct_shell_budget
end GVQCC.MeasuredDual
