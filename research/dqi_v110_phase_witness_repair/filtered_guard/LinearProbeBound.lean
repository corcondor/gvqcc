import Std

namespace GVQCC.LinearProbeBound

/-- Partition the nonzero support of an undetected difference between two legal
inputs. For very small support, a common disjoint part lifts the high side. -/
theorem split_difference (s : Nat) (hs : 0 < s) (hu : s ≤ 52) :
    ∃ a b c : Nat, a + b = s ∧ a + c ≤ 17 ∧
      18 ≤ b + c ∧ b + c ≤ 35 ∧ s + c ≤ 52 := by
  by_cases hl : s < 18
  · refine ⟨0, s, 18 - s, ?_, ?_, ?_, ?_, ?_⟩ <;> omega
  · by_cases hm : s ≤ 35
    · exact ⟨0, s, 0, by omega, by omega, by omega, by omega, by omega⟩
    · exact ⟨s - 35, 35, 0, by omega, by omega, by omega, by omega, by omega⟩

#print axioms split_difference
end GVQCC.LinearProbeBound
