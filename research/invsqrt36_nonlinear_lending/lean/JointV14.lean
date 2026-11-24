import Std
namespace GVQCC.JointV14
structure Delta where
  oldOps : Nat
  newOps : Nat
  oldPaid : Nat
  newPaid : Nat
  oldHMR : Nat
  newHMR : Nat
  deriving DecidableEq, Repr
def historyEconomy : Delta := ⟨1744,964,53,42,18,18⟩
def historyHub : Delta := ⟨1796,1063,57,62,22,22⟩
def gauge : Delta := ⟨193,176,12,18,7,2⟩
def applyCounts (ops paid hmr : Nat) (a b : Delta) : Nat × Nat × Nat :=
  (ops - a.oldOps - b.oldOps + a.newOps + b.newOps,
   paid - a.oldPaid - b.oldPaid + a.newPaid + b.newPaid,
   hmr - a.oldHMR - b.oldHMR + a.newHMR + b.newHMR)
-- These are totals extracted from exact native splice receipts.
theorem economyCounts : applyCounts 41868 1871 1186 historyEconomy gauge = (41071,1866,1181) := by decide
theorem hubCounts : applyCounts 41868 1871 1186 historyHub gauge = (41118,1882,1181) := by decide

-- Original source intervals and actual maximum native wire count of new bodies.
def gaugeCharts : List (Nat × Nat × Nat) :=
  [(21386,21431,35),(25112,25155,35),(26189,26233,35),
   (27227,27267,35),(27754,27783,35),(28272,28301,35)]
def historyCharts : List (Nat × Nat × Nat) :=
  [(22829,22859,33),(23357,23391,34),(24492,24524,32),(24953,24982,36)]
def coverage (cs : List (Nat × Nat × Nat)) : Nat :=
  cs.foldl (fun acc c => acc + (c.2.1 - c.1)) 0
def bounded (cs : List (Nat × Nat × Nat)) : Bool :=
  cs.all (fun c => decide (c.1 < c.2.1 ∧ c.2.2 ≤ 36))
def separated (cs ds : List (Nat × Nat × Nat)) : Bool :=
  cs.all (fun c => ds.all (fun d => decide (c.2.1 ≤ d.1 ∨ d.2.1 ≤ c.1)))
theorem chartLedger :
  bounded gaugeCharts = true ∧ bounded historyCharts = true ∧
  separated gaugeCharts historyCharts = true ∧
  55829 + coverage gaugeCharts = 56059 ∧
  55829 + coverage gaugeCharts + coverage historyCharts = 56184 := by decide
-- Score surrogate uses units of 1/16 expected paid gates.
theorem costWidthTradeoff : 27367 - 27111 = 256 := by decide
end GVQCC.JointV14
