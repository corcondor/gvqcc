import Std

namespace PackedAllGap

variable {R : Type}

theorem cancelCross (add : R → R → R) (zero : R)
    (assoc : ∀ a b c, add (add a b) c = add a (add b c))
    (comm : ∀ a b, add a b = add b a)
    (self : ∀ a, add a a = zero)
    (leftZero : ∀ a, add zero a = a)
    (a b c d : R) :
    add (add (add a b) c) (add b d) = add a (add d c) := by
  calc
    _ = add a (add b (add c (add b d))) := by simp only [assoc]
    _ = add a (add b (add b (add c d))) := by
      rw [← assoc c b d, comm c b, assoc b c d]
    _ = add a (add c d) := by
      rw [← assoc b b (add c d), self b, leftZero]
    _ = _ := by rw [comm c d]

theorem sylvesterLift (add mul : R → R → R) (zero : R)
    (aa : ∀ a b c, add (add a b) c = add a (add b c))
    (ac : ∀ a b, add a b = add b a)
    (az : ∀ a, add a a = zero)
    (al : ∀ a, add zero a = a)
    (ma : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (mc : ∀ a b, mul a b = mul b a)
    (dl : ∀ a b c, mul a (add b c) = add (mul a b) (mul a c))
    (dr : ∀ a b c, mul (add a b) c = add (mul a c) (mul b c))
    (A B q r p h t v k : R)
    (hB : B = add (mul q A) r)
    (hp : p = add (mul h A) t)
    (ht : t = add (mul r v) (mul A k)) :
    add (mul A (add (add h (mul q v)) k)) (mul B v) = p := by
  have hm : mul A (mul q v) = mul (mul q A) v := by
    rw [← ma A q v, mc A q]
  calc
    _ = add (add (add (mul A h) (mul A (mul q v))) (mul A k))
        (add (mul (mul q A) v) (mul r v)) := by simp only [hB, dl, dr]
    _ = add (mul A h) (add (mul r v) (mul A k)) := by
      rw [hm]
      exact cancelCross add zero aa ac az al _ _ _ _
    _ = p := by rw [mc A h, ← ht, ← hp]

theorem alignedIndex (n a j i : Nat) (ha : a ≤ n) (hj : j ≤ a)
    (ht : n - a + j ≤ n + i) (hi : a + i ≥ j) :
    a + i - j = n + i - (n - a + j) := by omega

theorem packedWords (n a : Nat) (h : a ≤ n) : n - a + a = n := by omega

theorem widthBudget : 865 + 16 + 1 + 18 = 900 := by decide

theorem hmrBranch (f m0 m1 : Bool) :
    (if f then m1 else m0) = Bool.xor (Bool.and (Bool.not f) m0) (Bool.and f m1) := by
  cases f <;> cases m0 <;> cases m1 <;> decide

#print axioms cancelCross
#print axioms sylvesterLift
#print axioms alignedIndex
#print axioms packedWords
#print axioms widthBudget
#print axioms hmrBranch

end PackedAllGap
