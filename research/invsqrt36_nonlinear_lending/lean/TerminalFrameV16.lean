import Std.Tactic
namespace GVQCC.TerminalFrameV16
-- Actual native receipt: defer a known unconditional restore to the output ABI.
def frame : List Nat := [33, 1, 2, 18, 13, 9, 6, 27, 8, 19, 10, 7, 12, 30, 14, 15, 16, 17, 11, 3, 20, 21, 22, 4, 24, 23, 26, 25, 28, 29, 0, 31, 32, 5, 34, 35, 36]
def invFrame : List Nat := [30, 1, 2, 19, 23, 33, 6, 11, 8, 5, 10, 18, 12, 4, 14, 15, 16, 17, 3, 9, 20, 21, 22, 25, 24, 27, 26, 7, 28, 29, 13, 31, 32, 0, 34, 35, 36]
def oldSwaps : List (Nat × Nat) := [(4, 23), (13, 4), (33, 0), (18, 3), (7, 11), (13, 25), (7, 18), (33, 30), (19, 9), (13, 27), (33, 13), (33, 7), (33, 19), (33, 5)]
def newSwaps : List (Nat × Nat) := [(33, 0), (18, 3), (13, 4), (9, 5), (27, 7), (19, 9), (27, 11), (30, 13), (27, 18), (27, 19)]
def sw (p : Nat × Nat) (i : Nat) : Nat :=
  if i = p.1 then p.2 else if i = p.2 then p.1 else i
def pullback (gs : List (Nat × Nat)) (i : Nat) : Nat :=
  gs.reverse.foldl (fun j p => sw p j) i
def finalLogicalIndex (i : Nat) : Nat := invFrame[pullback newSwaps i]!
theorem actual_frame : ∀ i : Fin 37, pullback oldSwaps i.val = frame[i.val]! := by decide
theorem inverse_frame : ∀ i : Fin 37, invFrame[frame[i.val]!]! = i.val := by decide
theorem terminal_indices : ∀ i : Fin 37,
    if i.val < 22 then finalLogicalIndex i.val = i.val else 22 ≤ finalLogicalIndex i.val := by decide
def payload (v : Nat → Bool) (i : Nat) : Bool := if i < 22 then v i else false
theorem terminal_abi (v : Nat → Bool) (i : Fin 37) :
    payload v (finalLogicalIndex i.val) = payload v i.val := by
  have h := terminal_indices i
  by_cases hi : i.val < 22
  · simp [hi] at h
    rw [h]
  · simp [hi] at h
    have hj : ¬ finalLogicalIndex i.val < 22 := by omega
    simp [payload, hi, hj]
theorem resource : oldSwaps.length = 14 ∧ newSwaps.length = 10 ∧
    40047 - oldSwaps.length + newSwaps.length = 40043 ∧
    oldSwaps.all (fun p => decide (p.1 < 36 ∧ p.2 < 36)) = true ∧
    newSwaps.all (fun p => decide (p.1 < 36 ∧ p.2 < 36)) = true := by decide
end GVQCC.TerminalFrameV16
