namespace GVQCCReciprocal

def parity : List Bool → Bool
  | [] => false
  | b :: bs => Bool.xor b (parity bs)

theorem conditional_distributivity (f a b : Bool) :
    (f && Bool.xor a b) = Bool.xor (f && a) (f && b) := by
  cases f <;> cases a <;> cases b <;> decide

theorem conditional_parity (f : Bool) (bs : List Bool) :
    (f && parity bs) = parity (bs.map (fun b => f && b)) := by
  induction bs with
  | nil => cases f <;> rfl
  | cons b bs ih =>
    simp only [parity, List.map_cons, conditional_distributivity, ih]

theorem affine_condition (f v : Bool) :
    (f && !v) = Bool.xor f (f && v) := by
  cases f <;> cases v <;> decide

theorem homogeneous_coset_shift (f s d : Bool) (h : (f && d) = false) :
    (f && Bool.xor s d) = (f && s) := by
  cases f <;> cases s <;> cases d <;> simp_all

theorem sibling_transport (f x : Bool) :
    Bool.xor (f && x) f = (f && !x) := by
  cases f <;> cases x <;> decide

theorem measurement_debt (m f v : Bool) :
    Bool.xor (m && (f && v)) (m && (f && v)) = false := by
  cases m <;> cases f <;> cases v <;> decide

end GVQCCReciprocal
