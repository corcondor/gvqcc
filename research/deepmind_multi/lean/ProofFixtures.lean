import GVQCCMicro

namespace GVQCCLean
-- The same interpreter and cost model used by the generated window proofs.
example : nonCliffordCost [.ccx 0 1 2, .cz 2 3, .ccx 0 1 2] = 2 := by
  decide
example : nonCliffordCost [.cz 2 3, .ccz 0 1 3] = 1 := by
  decide
example : ccxCost [.ccx 0 1 2, .ccx 0 1 3] = 2 := by
  decide
end GVQCCLean
