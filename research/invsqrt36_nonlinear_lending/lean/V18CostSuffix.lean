import Std.Tactic
namespace GVQCC.V18CostSuffix

-- Actual 37-coordinate interface and native SWAP list from the exact receipt.
def entryFrame : List Nat :=
  [22,9,31,25,1,21,19,28,18,17,10,16,33,32,24,3,6,20,0,23,15,34,27,26,29,4,35,7,8,13,5,2,14,11,30,36,12]
def restore : List (Nat × Nat) :=
  [(22,0),(9,1),(31,2),(25,3),(9,4),(21,5),(19,6),(28,7),(18,8),(17,9),
   (16,11),(33,12),(32,13),(24,14),(25,15),(19,16),(20,17),(22,18),(23,19),
   (25,20),(34,21),(27,22),(26,23),(29,24),(35,26),(28,27),(32,29),(34,30),(35,33),(36,35)]
def sw (p : Nat × Nat) (i : Nat) : Nat :=
  if i = p.1 then p.2 else if i = p.2 then p.1 else i
def pullback (gs : List (Nat × Nat)) (i : Nat) : Nat :=
  gs.reverse.foldl (fun j p => sw p j) i
theorem actual_restore : ∀ i : Fin 37, pullback restore i.val = entryFrame[i.val]! := by decide
theorem restored_payload (physical : Nat → Bool) (i : Fin 37) :
    physical (pullback restore i.val) = physical entryFrame[i.val]! := by
  rw [actual_restore i]

-- HMR on an exact zero wire has zero phase for either random result.
-- Reachability of that zero premise is independently proved by the BDD.
theorem clean_hmr (m phase : Bool) :
    Bool.xor phase (false && m) = phase := by cases m <;> cases phase <;> decide

-- Semantic-interface congruence for an identical deterministic suffix given
-- the same subsequent measurement transcript.
theorem suffix_congruence {S E : Type} (step : S → E → S)
    (a b : S) (events : List E) (h : a = b) :
    events.foldl step a = events.foldl step b := by rw [h]

-- Expected paid-gate counts in units of 1/16; receipt arithmetic only.
theorem resource_receipt :
    restore.length = 30 ∧
    restore.all (fun p => decide (p.1 < 37 ∧ p.2 < 37)) = true ∧
    5635 + 30 + 1 + 4 + 53497 = 59167 ∧
    412*16 + 15909 = 22501 ∧
    417*16 + 15909 = 22581 ∧
    26687 - 22581 = 4106 ∧
    47638 - 7410 + 7772 = 48000 := by decide
end GVQCC.V18CostSuffix
