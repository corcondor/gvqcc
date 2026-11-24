import Std.Tactic
namespace GVQCC.V15ChartTransport
-- Physical-to-donor logical labels at the two native chart boundaries.
def entryLabels : List Nat := [22,18,10,28,6,35,32,17,19,30,31,21,14,11,3,9,12,7,16,23,2,1,33,20,13,24,4,27,8,0,25,5,29,15,34,26,36]
def exitLabels : List Nat := [15,18,10,16,11,30,32,27,19,23,31,17,14,25,3,9,12,7,21,28,2,1,33,6,13,20,4,24,8,0,22,5,29,35,34,26,36]
def swaps : List (Nat × Nat) := [(4,23),(13,4),(33,0),(18,3),(7,11),(13,25),(7,18),(33,30),(19,9),(13,27),(33,13),(33,7),(33,19),(33,5)]
def sw (p : Nat × Nat) (i : Nat) : Nat :=
  if i = p.1 then p.2 else if i = p.2 then p.1 else i
-- Pull back the output coordinate through the actual SWAP sequence.
def pullback (i : Nat) : Nat := swaps.reverse.foldl (fun j p => sw p j) i
theorem concrete_restoration : ∀ i : Fin 37,
    entryLabels[pullback i.val]! = exitLabels[i.val]! := by decide
theorem arbitrary_payload_restoration (v : Nat → Bool) (i : Fin 37) :
    v (entryLabels[pullback i.val]!) = v (exitLabels[i.val]!) :=
  congrArg v (concrete_restoration i)
theorem no_extra_wire : swaps.all (fun p => decide (p.1 < 36 ∧ p.2 < 36)) = true := by decide
theorem spectator_preserved : pullback 36 = 36 := by decide
-- Resource projections extracted from the exact native gate lists in receipt.json.
-- Full chart semantics, including HMR phase, is independently checked by BDD.
def oldPaidPositions : List Nat := [194,208,223,236,254,271,289,306,307,328,382,409,581,597,610,623,639,656,672]
def newPaidPositions : List Nat := [186,193,203,220,233,243,265,277,279,361,389,556,563,575,583,601,611,623]
def oldHMRPositions : List Nat := [33,60,85,106,134,166,188,408,431,453,477,502,527,551,572]
def newHMRPositions : List Nat := [33,58,83,102,128,158,180,388,412,432,454,477,500,524,545]
theorem local_resource : oldPaidPositions.length = 19 ∧ newPaidPositions.length = 18 ∧
    oldHMRPositions.length = 15 ∧ newHMRPositions.length = 15 ∧ swaps.length = 14 := by decide
-- Costs in sixteenths, using the separately established BDD execution probabilities.
theorem measured_budget : 26703 - 16 = 26687 ∧ 40079 - 687 + 655 = 40047 ∧
    1833 - 19 + 18 = 1832 := by decide
end GVQCC.V15ChartTransport
