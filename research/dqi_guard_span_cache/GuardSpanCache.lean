import Std
namespace GuardSpanCache

def parity : List Bool → Bool
  | [] => false
  | a :: xs => Bool.xor a (parity xs)

theorem guard_xor (g a b : Bool) :
    (g && Bool.xor a b) = Bool.xor (g && a) (g && b) := by
  cases g <;> cases a <;> cases b <;> decide

theorem guard_parity (g : Bool) (xs : List Bool) :
    parity (xs.map (fun x => g && x)) = (g && parity xs) := by
  induction xs with
  | nil => cases g <;> decide
  | cons a xs ih =>
    change Bool.xor (g && a) (parity (xs.map (fun x => g && x))) = (g && Bool.xor a (parity xs))
    rw [ih, guard_xor]

theorem guarded_product (g a b : Bool) :
    ((g && a) && b) = (g && (a && b)) := by
  cases g <;> cases a <;> cases b <;> decide

theorem guarded_update (g a b t : Bool) :
    Bool.xor t ((g && a) && b) = Bool.xor t (g && (a && b)) := by
  rw [guarded_product]

theorem debt_factor (g m a : Bool) :
    (m && (g && a)) = ((m && g) && a) := by
  cases g <;> cases m <;> cases a <;> decide

theorem debt_list (g : Bool) (xs : List (Bool × Bool)) :
    parity (xs.map (fun p => p.1 && (g && p.2))) =
    parity (xs.map (fun p => (p.1 && g) && p.2)) := by
  have h : (fun p : Bool × Bool => p.1 && (g && p.2)) =
      (fun p : Bool × Bool => (p.1 && g) && p.2) := by
    funext p
    exact debt_factor g p.1 p.2
  rw [h]

theorem xor_self_zero (a : Bool) : Bool.xor a a = false := by
  cases a <;> decide

theorem debt_cancel (g : Bool) (xs : List (Bool × Bool)) :
    Bool.xor (parity (xs.map (fun p => p.1 && (g && p.2))))
      (parity (xs.map (fun p => (p.1 && g) && p.2))) = false := by
  rw [debt_list, xor_self_zero]

theorem inactive_ccx (a b t : Bool) :
    Bool.xor t (false && (a && b)) = t := by
  cases t <;> decide

abbrev Term := Nat × Nat × Nat
abbrev Group := List Nat × List Term
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

def groups : List Group :=
  [([1947,3943,3982,2617,2282,3165],
     [(40,1636,382),(24,723,1869),(56,3726,1587),(16,2282,1283),
      (8,2617,590),(32,3165,1149),(1,1947,3615),(6,233,1984),
      (7,1906,1628),(2,3943,412),(3,2300,3971),(4,3982,2115)]),
   ([2896,984,160,2016,1697,272],
     [(4,160,2936),(7,2088,1070),(3,2184,2791),(32,272,2801),
      (24,321,1468),(56,81,3917),(40,1776,535),(8,2016,3418),
      (16,1697,1963),(5,3056,415),(1,2896,3785),(2,984,1457)]),
   ([4027,1877,2162,608,3439,592],
     [(40,48,3115),(32,592,879),(8,608,1629),(24,3855,2329),
      (16,3439,1330),(3,2286,2546),(6,3879,2843),(1,4027,745),
      (2,1877,2042),(7,156,3592),(4,2162,3297),(56,3423,2678)]),
   ([714,701,393],
     [(4,393,874),(1,714,1033),(3,119,1891),(2,701,2106),
      (6,820,2896),(7,510,3123)])]

def decode : List Nat → Nat → Nat
  | [], _ => 0
  | b :: bs, c => Nat.xor (if c % 2 = 1 then b else 0) (decode bs (c / 2))

def expanded : List Term :=
  groups.flatMap (fun g => g.2.map (fun t => (decode g.1 t.1, t.2.1, t.2.2)))

set_option maxRecDepth 10000 in
set_option maxHeartbeats 0 in
theorem exact_old_coverage : original.all (fun t => expanded.contains t) = true := by decide

set_option maxRecDepth 10000 in
set_option maxHeartbeats 0 in
theorem exact_new_coverage : expanded.all (fun t => original.contains t) = true := by decide

set_option maxRecDepth 10000 in
set_option maxHeartbeats 0 in
theorem exact_lengths : original.length = 42 ∧ expanded.length = 42 := by decide

theorem rank_sum : groups.foldl (fun s g => s + g.1.length) 0 = 21 := by decide

theorem scratch_bound : groups.all (fun g => g.1.length <= 6) = true := by decide

theorem isolated_ccx_count : 42 + 21 = (63 : Nat) := by decide

#print axioms guard_xor
#print axioms guard_parity
#print axioms guarded_product
#print axioms guarded_update
#print axioms debt_factor
#print axioms debt_list
#print axioms xor_self_zero
#print axioms debt_cancel
#print axioms inactive_ccx
#print axioms exact_old_coverage
#print axioms exact_new_coverage
#print axioms exact_lengths
#print axioms rank_sum
#print axioms scratch_bound
#print axioms isolated_ccx_count
end GuardSpanCache
