import Lean

namespace GVQCC.PhysicalPivot

-- Endpoint coordinates: i is the start, j the next continuation boundary.
-- No field axioms are needed to share the same physical reciprocal.
def pivot (i j : Nat) : Nat := i + j - 1

theorem pivot_strict {i j k : Nat} (hij : i < j) (hjk : j < k) :
    pivot i j < pivot j k := by
  unfold pivot
  omega

theorem pivot_bound {i j : Nat} (hij : i < j) (hj : j ≤ 35) :
    pivot i j < 69 := by
  unfold pivot
  omega

theorem recover_boundary {i j : Nat} (hij : i < j) :
    pivot i j + 1 - i = j := by
  unfold pivot
  omega

theorem reciprocal_slice {i k : Nat} (hk : 0 < k) :
    71 - 2*i - k = 70 - pivot i (i+k) := by
  unfold pivot
  omega

theorem recover_disjoint {i j k : Nat} (hij : i < j) (hik : i < k)
    (h : pivot i j = pivot i k) : j = k := by
  unfold pivot at h
  omega

#print axioms pivot_strict
#print axioms pivot_bound
#print axioms recover_boundary
#print axioms reciprocal_slice
#print axioms recover_disjoint
end GVQCC.PhysicalPivot
