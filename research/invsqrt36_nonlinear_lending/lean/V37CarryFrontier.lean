import Std.Tactic
namespace GVQCC.V37

-- Output-basis transvection, one nonlinear update serves two outputs.
theorem output_basis (a b f g : Bool) :
    let u := Bool.xor a b
    let v := b
    let u' := Bool.xor u (Bool.xor f g)
    let v' := Bool.xor v g
    (Bool.xor u' v', v') = (Bool.xor a f, Bool.xor b g) := by
  cases a <;> cases b <;> cases f <;> cases g <;> decide

theorem shared_output (a b f : Bool) :
    let u := Bool.xor a b
    let v := Bool.xor b f
    (Bool.xor u v, v) = (Bool.xor a f, Bool.xor b f) := by
  cases a <;> cases b <;> cases f <;> decide

-- HMR of t with correction controlled by m; residual l is reconstructed.
theorem affine_residue (t a b l m : Bool)
    (h : Bool.xor t (a && b) = l) :
    (Bool.xor (m && t) (Bool.xor (m && a && b) (m && l)) = false) ∧
    Bool.xor t (a && b) = l := by
  cases t <;> cases a <;> cases b <;> cases l <;> cases m <;> (first | decide | contradiction)

-- Actual source instructions 291 and 40692; the reachable premise is
-- certified by independent BDD replay, not asserted as a universal identity.
theorem actual291 (q15 q21 q32 m : Bool)
    (h : Bool.xor q32 (q15 && q21) = q15) :
    Bool.xor (m && q32) (Bool.xor (m && q15 && q21) (m && q15)) = false :=
  (affine_residue q32 q15 q21 q15 m h).1

theorem actual40692 (q31 q27 q25 q19 q29 m : Bool)
    (h : Bool.xor q25 (q31 && q27) = Bool.xor q19 q29) :
    Bool.xor (m && q25) (Bool.xor (m && q31 && q27) (m && Bool.xor q19 q29)) = false :=
  (affine_residue q25 q31 q27 (Bool.xor q19 q29) m h).1

theorem carry_mask (a b c : Bool) :
    Bool.xor c (a && b) =
      Bool.xor ((Bool.xor a c) && b) (c && !b) := by
  cases a <;> cases b <;> cases c <;> decide

-- Transport of the phase liability over two consecutive writes.
theorem two_write_debt (m q f g : Bool) :
    Bool.xor (m && q) (m && Bool.xor (Bool.xor q f) g) =
      Bool.xor (m && f) (m && g) := by
  cases m <;> cases q <;> cases f <;> cases g <;> decide

theorem resource_certificate :
    23215 - 2 * 16 = 23183 ∧
    3343 - 98 = 3245 ∧
    51383 + 10 + 5 = 51398 ∧
    1601 - 2 = 1599 ∧
    19 + 1 = 20 ∧
    1288 + 2 = 1290 := by decide
end GVQCC.V37
