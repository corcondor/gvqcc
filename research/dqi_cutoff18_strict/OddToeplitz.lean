import Mathlib

namespace GVQCC.OddToeplitz

-- Exact index correspondence for c,G0,J0,G1,J1,...
theorem even_to_odd (i j : Nat) (h : i ≤ j) :
    (2*j+1-2*i-1)/2 = j-i := by omega

theorem odd_to_even (i j : Nat) (h : i ≤ j) :
    (2*j+2-(2*i+1)-1)/2 = j-i := by omega

-- The disjoint cross rectangle is the only additional part at a binary split.
theorem split_pairs (i j k : Nat) (h : i < j) :
    (i < k ∧ j < k) ∨ (i < k ∧ k ≤ j) ∨ (k ≤ i ∧ k ≤ j) := by omega

theorem split_exclusive (i j k : Nat) :
    ¬ ((i < k ∧ j < k) ∧ (i < k ∧ k ≤ j)) := by omega

theorem split_exclusive₂ (i j k : Nat) :
    ¬ ((i < k ∧ k ≤ j) ∧ (k ≤ i ∧ k ≤ j)) := by omega

theorem split_exclusive₃ (i j k : Nat) :
    ¬ ((i < k ∧ j < k) ∧ (k ≤ i ∧ k ≤ j)) := by omega

-- Characteristic-two reversible update, arbitrary dirty target.
theorem undo (x y t : Bool) : Bool.xor (Bool.xor t (x && y)) (x && y) = t := by
    cases x <;> cases y <;> cases t <;> decide

-- The numerical budget uses a separately checked DP schedule and compiler.
theorem m17_budget : 42 * (2*54+129) + 546 = (10500 : Nat) := by decide

#print axioms even_to_odd
#print axioms odd_to_even
#print axioms split_pairs
#print axioms split_exclusive
#print axioms split_exclusive₂
#print axioms split_exclusive₃
#print axioms undo
#print axioms m17_budget
end GVQCC.OddToeplitz
