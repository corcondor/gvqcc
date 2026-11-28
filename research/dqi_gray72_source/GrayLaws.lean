import Std
namespace GrayLaws
theorem relativeGauge (r oldLam oldProd newLam newProd : Bool) :
    (((r ^^ oldLam) ^^ oldProd) ^^ (oldLam ^^ newLam)) ^^ (oldProd ^^ newProd) =
    (r ^^ newLam) ^^ newProd := by
  cases r <;> cases oldLam <;> cases oldProd <;> cases newLam <;> cases newProd <;> decide
theorem grayStep (v oldContribution newContribution : Bool) :
    (v ^^ oldContribution) ^^ (oldContribution ^^ newContribution) =
    v ^^ newContribution := by
  cases v <;> cases oldContribution <;> cases newContribution <;> decide
theorem doubleInvert (b : Bool) : (!(!b)) = b := by cases b <;> decide
#print axioms relativeGauge
#print axioms grayStep
#print axioms doubleInvert
end GrayLaws
