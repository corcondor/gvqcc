import Std
namespace V11CostBudget
def publicPaid : Nat := 22501
def costBody : Nat := 24553
def costOutside : Nat := 2364
def costPaid : Nat := 26917
def wideBody : Nat := 24953
def wideOutside : Nat := 2268
def widePaid : Nat := 27221
-- Arithmetic of independently measured resource receipts; not a proof of BDD.
theorem costSplit : costBody + costOutside = costPaid := by decide
theorem wideSplit : wideBody + wideOutside = widePaid := by decide
theorem arity3Cost : 1749 + 59 + 44 = (1852 : Nat) := by decide
theorem arity3Wide : 1759 + 79 + 44 = (1882 : Nat) := by decide
-- r is rotation cost in integer sixteenth-gate units, <= 241 * 16.
theorem fixedBodiesCannotWin (r : Nat) (hr : r <= 3856) :
    37 * (22501 + r) < 36 * (24553 + r) := by omega
theorem necessaryBodyReduction (r b : Nat) (hr : r <= 3856)
    (hwin : 36 * (b + r) < 37 * (22501 + r)) : b + 1320 <= 24553 := by omega
theorem necessaryTotalReduction (r e : Nat) (hr : r <= 3856)
    (hwin : 36 * (e + r) < 37 * (22501 + r)) : e + 3684 <= 26917 := by omega
end V11CostBudget
