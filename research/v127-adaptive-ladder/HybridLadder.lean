import Init
namespace GVQCC.V127

def bx (a b : Bool) : Bool := Bool.xor a b
def andList : List Bool → Bool
 | [] => true
 | a::as => a && andList as

theorem andList_append (a b : List Bool) : andList (a ++ b) = (andList a && andList b) := by
 induction a with
 | nil => simp [andList]
 | cons x xs ih => cases x <;> simp [andList,ih]

theorem split_prefix (a b : List Bool) (t : Bool) :
 bx t (andList (a ++ b)) = bx t (andList a && andList b) := by
 rw [andList_append]

theorem erase_ancilla (a b m : Bool) : bx (m && (a && b)) (m && (a && b)) = false := by
 cases a <;> cases b <;> cases m <;> decide

theorem transposed_mask (a b m n : Bool) :
 bx (m && a) (n && bx a b) = bx ((bx m n) && a) (n && b) := by
 cases a <;> cases b <;> cases m <;> cases n <;> decide

theorem controlled_add (h a z : Bool) :
 bx z (h && a) = if h then bx z a else z := by
 cases h <;> cases a <;> cases z <;> decide

end GVQCC.V127
#print axioms GVQCC.V127.andList_append
#print axioms GVQCC.V127.split_prefix
#print axioms GVQCC.V127.erase_ancilla
#print axioms GVQCC.V127.transposed_mask
#print axioms GVQCC.V127.controlled_add
