import Std
namespace CoherentCursor

/-- Interleave a zero tag in each skipped pair. The first pair has a nonzero
    scalar tag. The nonzero scalar is not copied into another register. -/
def taggedTail (z : α) : List α → List (α × α)
  | [] => []
  | y :: ys => (z,y) :: taggedTail z ys

def tagged (z a h : α) (hs : List α) : List (α × α) :=
  (a,h) :: taggedTail z hs

theorem taggedTail_snd (z : α) (hs : List α) :
    (taggedTail z hs).map Prod.snd = hs := by
  induction hs with
  | nil => rfl
  | cons y ys ih => simp [taggedTail, ih]

theorem taggedTail_fst (z : α) (hs : List α) :
    (taggedTail z hs).map Prod.fst = List.replicate hs.length z := by
  induction hs with
  | nil => rfl
  | cons y ys ih => simp [taggedTail, ih]

theorem tagged_decode (z a h : α) (hs : List α) :
    (tagged z a h hs).map Prod.snd = h :: hs := by
  simp [tagged, taggedTail_snd]

theorem tag_markers (z a h : α) (hs : List α) :
    (tagged z a h hs).map Prod.fst = a :: List.replicate hs.length z := by
  simp [tagged, taggedTail_fst]

theorem tag_capacity (z : α) (hs : List α) :
    (taggedTail z hs).length = hs.length := by
  induction hs with
  | nil => rfl
  | cons y ys ih => simp [taggedTail, ih]

theorem tag_injective (z a b h k : α) (hs ks : List α)
    (e : tagged z a h hs = tagged z b k ks) :
    a = b ∧ h = k ∧ hs = ks := by
  have e1 := congrArg (fun x : List (α × α) => x.map Prod.snd) e
  have e2 := congrArg (fun x : List (α × α) => x.map Prod.fst) e
  rw [tagged_decode, tagged_decode] at e1
  rw [tag_markers, tag_markers] at e2
  exact ⟨(List.cons.inj e2).1, (List.cons.inj e1).1, (List.cons.inj e1).2⟩

theorem next_bound (h v q : Nat) (hv : v < q-h) :
    h < h+v+1 ∧ h+v+1 ≤ q := by omega

theorem reverse_valuation (h v : Nat) : (h+v+1)-h-1 = v := by omega

theorem skipped_pair (h v i : Nat) (hi : h < i) (hj : i < h+v+1) :
    i ≠ h ∧ i ≠ h+v+1 := by omega

theorem reverse_endpoint (h v j : Nat) (e : j = h+v+1) :
    h+(j-h-1)+1 = j := by omega

theorem cursor_xor_inverse (h j : Bool) :
    ((h ^^ (h ^^ j)) ^^ (h ^^ j)) = h := by
  cases h <;> cases j <;> decide

theorem masked_update_involution (on x y : Bool) :
    ((x ^^ (on && y)) ^^ (on && y)) = x := by
  cases on <;> cases x <;> cases y <;> decide

theorem hmr_bilinear_repay (s x y : Bool) :
    ((s && (x && y)) ^^ (s && x && y)) = false := by
  cases s <;> cases x <;> cases y <;> decide

#print axioms taggedTail_snd
#print axioms taggedTail_fst
#print axioms tagged_decode
#print axioms tag_markers
#print axioms tag_capacity
#print axioms tag_injective
#print axioms next_bound
#print axioms reverse_valuation
#print axioms skipped_pair
#print axioms reverse_endpoint
#print axioms cursor_xor_inverse
#print axioms masked_update_involution
#print axioms hmr_bilinear_repay
end CoherentCursor
