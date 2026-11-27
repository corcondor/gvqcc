import Mathlib

namespace GVQCC.BranchCollision

variable {A : Type*} [AddCommGroup A]

/-- The transformed syndrome alone cannot distinguish zero input on the low
chart from a legal high-weight input already equal to the padding. -/
def eraseTag (low : A → Bool) (pad : A) (x : A) : A :=
  if low x then x + pad else x

theorem padding_collision (low : A → Bool) (pad : A)
    (h0 : low 0 = true) (hp : low pad = false) :
    eraseTag low pad 0 = eraseTag low pad pad := by
  simp [eraseTag, h0, hp]

theorem padding_not_injective (low : A → Bool) (pad : A)
    (h0 : low 0 = true) (hp : low pad = false) (hn : pad ≠ 0) :
    ¬ Function.Injective (eraseTag low pad) := by
  intro hi
  exact hn (hi (padding_collision low pad h0 hp)).symm

/-- Rotation on the high branch does not remove the tag collision:
the inverse rotation of the padding is another legal high-weight input. -/
def eraseRotatedTag (low : A → Bool) (pad : A) (T : A ≃ A) (x : A) : A :=
  if low x then x + pad else T x

theorem rotated_padding_collision (low : A → Bool) (pad : A) (T : A ≃ A)
    (h0 : low 0 = true) (hp : low (T.symm pad) = false) :
    eraseRotatedTag low pad T 0 = eraseRotatedTag low pad T (T.symm pad) := by
  simp [eraseRotatedTag, h0, hp]

theorem rotated_padding_not_injective (low : A → Bool) (pad : A) (T : A ≃ A)
    (h0 : low 0 = true) (hp : low (T.symm pad) = false)
    (hn : T.symm pad ≠ 0) :
    ¬ Function.Injective (eraseRotatedTag low pad T) := by
  intro hi
  exact hn (hi (rotated_padding_collision low pad T h0 hp)).symm

/-- Retaining a tag, or an equivalent encoding, is sufficient to invert
each of the three chart transformations on the syndrome. -/
def encode (pad1 pad2 : A) (T : A ≃ A) (tag : Fin 3) (x : A) : Fin 3 × A :=
  (tag, if tag = 0 then T x else if tag = 1 then x+pad1 else x+pad2)

def decode (pad1 pad2 : A) (T : A ≃ A) (y : Fin 3 × A) : A :=
  if y.1 = 0 then T.symm y.2 else if y.1 = 1 then y.2-pad1 else y.2-pad2

theorem tagged_roundtrip (pad1 pad2 : A) (T : A ≃ A) (tag : Fin 3) (x : A) :
    decode pad1 pad2 T (encode pad1 pad2 T tag x) = x := by
  by_cases h0 : tag = 0
  · simp [encode, decode, h0]
  · by_cases h1 : tag = 1
    · simp [encode, decode, h0, h1]
    · simp [encode, decode, h0, h1]

theorem tag_phase_repay (tag m phase : Bool) :
    Bool.xor (Bool.xor phase (m && tag)) (m && tag) = phase := by
  cases tag <;> cases m <;> cases phase <;> decide

end GVQCC.BranchCollision

#print axioms GVQCC.BranchCollision.padding_collision
#print axioms GVQCC.BranchCollision.padding_not_injective
#print axioms GVQCC.BranchCollision.rotated_padding_collision
#print axioms GVQCC.BranchCollision.rotated_padding_not_injective
#print axioms GVQCC.BranchCollision.tagged_roundtrip
#print axioms GVQCC.BranchCollision.tag_phase_repay
