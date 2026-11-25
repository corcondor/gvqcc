import Std.Tactic
namespace GVQCC.V41

-- The determinant is computed over GF(2). These are Cramer's numerators,
-- not division by a possibly zero determinant.
theorem cramer_numerators (a b c d x y : Bool) :
    let det := Bool.xor (a && d) (b && c)
    let r := Bool.xor (a && x) (b && y)
    let s := Bool.xor (c && x) (d && y)
    (Bool.xor (d && r) (b && s) = (det && x)) ∧
    (Bool.xor (a && s) (c && r) = (det && y)) := by
  cases a <;> cases b <;> cases c <;> cases d <;>
    cases x <;> cases y <;> decide

-- The exceptional case is repaired, never postselected away.
theorem glue (d x repair : Bool)
    (h : (!d && repair) = (!d && x)) :
    Bool.xor (d && x) (!d && repair) = x := by
  rw [h]
  cases d <;> cases x <;> decide

theorem cofactor_two (a b x : Bool) :
    Bool.xor (a && x) (!a && b && x) = ((a || b) && x) := by
  cases a <;> cases b <;> cases x <;> decide

theorem cofactor_glue (a b x repair : Bool)
    (h : (!(a || b) && repair) = (!(a || b) && x)) :
    Bool.xor (Bool.xor (a && x) (!a && b && x))
      (!(a || b) && repair) = x := by
  rw [cofactor_two, h]
  cases a <;> cases b <;> cases x <;> decide

-- Actual projection direction at node 721: e_4 + e_24.
-- The retained coordinate is the XOR; its companion is reconstructed.
theorem affine_direction (a b : Bool) :
    Bool.xor (Bool.xor a b) a = b := by
  cases a <;> cases b <;> decide

theorem direction_derivative (a b u v : Bool) :
    Bool.xor ((Bool.xor a u) && (Bool.xor b v)) (a && b) =
      Bool.xor (Bool.xor (a && v) (b && u)) (u && v) := by
  cases a <;> cases b <;> cases u <;> cases v <;> decide

-- Deterministic measurement erasure on the graph of a decoder.
theorem erasure_sign (m q f : Bool) (h : q = f) :
    Bool.xor (m && q) (m && f) = false := by
  rw [h]; cases m <;> cases f <;> decide

theorem projection_injective {X Y : Type} (project : X → Y) (decode : Y → X)
    (h : ∀ x, decode (project x) = x) :
    Function.Injective project := by
  intro x y hxy
  calc
    x = decode (project x) := (h x).symm
    _ = decode (project y) := congrArg decode hxy
    _ = y := h y

-- An exact zero relation is in every restricted domain kernel.
theorem restrict_kernel {X : Type} (P : X → Bool) (D S : X → Prop)
    (sub : ∀ x, S x → D x)
    (h : ∀ x, D x → P x = false) :
    ∀ x, S x → P x = false := by
  intro x hx
  exact h x (sub x hx)

theorem weighted_edges (a b c k l : Bool) :
    Bool.xor (k && Bool.xor a b) (l && Bool.xor b c) =
      Bool.xor (Bool.xor (k && a) (Bool.xor k l && b)) (l && c) := by
  cases a <;> cases b <;> cases c <;> cases k <;> cases l <;> decide

theorem counts :
    18 + 1 + 1 = 20 ∧
    3129357 + 4095 = 3133452 ∧
    3003852 + 129600 = 3133452 ∧
    262109 + 2871343 = 3133452 ∧
    16777232 = 2^4 + 2^24 := by decide

end GVQCC.V41
