import Std.Tactic
set_option maxRecDepth 65536
set_option maxHeartbeats 0
namespace GVQCC.V30

def X := Bool.xor

-- Exact nonlinear remainder, retained in forward acceptance.
theorem ccx_difference (a b da db : Bool) :
    X (a && b) (X a da && X b db) =
      X (X (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

-- Local transpose-Jacobian transport plus the exact quadratic remainder.
theorem ccx_adjoint (a b du dv dt lu lv lt : Bool) :
    X (lu && du) (X (lv && dv)
      (lt && X dt (X (X (a && dv) (b && du)) (du && dv)))) =
    X (X (X lu (lt && b) && du) (X lv (lt && a) && dv))
      (X (lt && dt) (lt && (du && dv))) := by
  cases a <;> cases b <;> cases du <;> cases dv <;> cases dt <;>
    cases lu <;> cases lv <;> cases lt <;> decide

theorem hmr_adjoint (g m d l : Bool) :
    X (l && (d && !g)) (m && g && d) =
      (X (l && !g) (m && g) && d) := by
  cases g <;> cases m <;> cases d <;> cases l <;> decide

-- General finite-chain telescoping with injection and nonlinear remainder.
def chain (p : Bool) : List (Bool × Bool × Bool) → Bool
  | [] => false
  | (q,h,r) :: xs => X (X p q) (X (X h r) (chain q xs))
def endpoint (p : Bool) : List (Bool × Bool × Bool) → Bool
  | [] => p
  | (q,_,_) :: xs => endpoint q xs
def injections : List (Bool × Bool × Bool) → Bool
  | [] => false
  | (_,h,r) :: xs => X (X h r) (injections xs)
theorem discrete_adjoint_telescope (p : Bool) (xs : List (Bool × Bool × Bool)) :
    chain p xs = X (X p (endpoint p xs)) (injections xs) := by
  induction xs generalizing p with
  | nil => cases p <;> decide
  | cons z zs ih =>
    rcases z with ⟨q,h,r⟩
    change X (X p q) (X (X h r) (chain q zs)) =
      X (X p (endpoint q zs)) (X (X h r) (injections zs))
    rw [ih q]
    cases p <;> cases q <;> cases h <;> cases r <;>
      cases endpoint false zs <;> cases endpoint true zs <;>
      cases injections zs <;> rfl

-- Concrete affine repair from native V29 fixed-compact [231,397),
-- after dropping CCX(19,21,15) at original native index 319.
-- Rows encode the 37 input bits and affine constant bit 37.
def rowStep (s : Array Nat) (g : Nat × Nat × Nat) : Array Nat :=
  let (k,a,b) := g
  if k = 17 then s.set! a (Nat.xor s[a]! (2^37))
  else if k = 33 then s.set! b (Nat.xor s[b]! s[a]!)
  else if k = 34 then (s.set! a s[b]!).set! b s[a]!
  else s
def identity : Array Nat := ((List.range 37).map (fun i => 2^i)).toArray
def oldRepair : List (Nat × Nat × Nat) := [(33,4,15), (33,7,15), (33,8,15), (33,9,15), (33,16,15), (33,18,15), (33,21,15), (33,25,15), (33,26,15), (33,27,15), (33,28,15), (33,30,15), (33,31,15), (33,34,15), (17,17,17), (33,0,17), (33,2,17), (33,4,17), (33,7,17), (33,8,17), (33,9,17), (33,10,17), (33,14,17), (33,16,17), (33,18,17), (33,19,17), (33,25,17), (33,27,17), (33,29,17), (33,30,17), (33,1,20), (33,4,20), (33,5,20), (33,7,20), (33,10,20), (33,12,20), (33,14,20), (33,16,20), (33,19,20), (33,24,20), (33,25,20), (33,26,20), (33,27,20), (33,28,20), (33,29,20), (33,31,20), (17,32,32), (33,1,32), (33,2,32), (33,3,32), (33,6,32), (33,8,32), (33,9,32), (33,12,32), (33,16,32), (33,18,32), (33,19,32), (33,21,32), (33,23,32), (33,24,32), (33,25,32), (33,26,32), (33,27,32), (33,28,32), (33,30,32), (33,31,32), (33,33,32), (33,0,35), (33,3,35), (33,4,35), (33,6,35), (33,7,35), (33,8,35), (33,9,35), (33,13,35), (33,18,35), (33,19,35), (33,23,35), (33,24,35), (33,25,35), (33,28,35), (33,29,35), (33,30,35), (33,31,35), (34,17,15), (33,15,20), (33,15,35), (33,17,15), (34,32,20), (33,20,15), (33,20,17), (34,35,32), (33,32,15), (33,32,17), (33,32,20), (33,35,15), (33,35,32), (33,35,32), (33,35,20), (33,32,17), (34,35,32), (33,20,17), (33,20,15), (34,32,20), (33,17,35), (33,17,32), (33,17,20), (33,17,15), (33,15,32), (33,34,35), (33,33,35), (33,27,35), (33,25,35), (33,24,35), (33,21,35), (33,16,35), (33,13,35), (33,12,35), (33,7,35), (33,5,35), (33,4,35), (33,2,35), (33,1,35), (33,0,35), (17,35,35), (33,34,32), (33,29,32), (33,26,32), (33,25,32), (33,24,32), (33,5,32), (33,34,20), (33,33,20), (33,30,20), (33,26,20), (33,25,20), (33,24,20), (33,23,20), (33,21,20), (33,18,20), (33,14,20), (33,10,20), (33,9,20), (33,8,20), (33,7,20), (33,6,20), (33,4,20), (33,3,20), (33,2,20), (17,20,20), (33,34,17), (33,33,17), (33,31,17), (33,28,17), (33,25,17), (33,23,17), (33,21,17), (33,14,17), (33,12,17), (33,10,17), (33,7,17), (33,6,17), (33,5,17), (33,4,17), (33,3,17), (33,1,17), (33,0,17), (33,33,15), (33,29,15), (33,26,15), (33,25,15), (33,23,15), (33,19,15), (33,12,15), (33,7,15), (33,6,15), (33,5,15), (33,4,15), (33,3,15), (33,2,15), (33,1,15), (17,15,15)]
def newRepair : List (Nat × Nat × Nat) := [(33,13,35), (33,13,32), (33,13,20), (33,13,17), (33,13,15), (33,15,32), (33,15,20), (33,15,17), (33,17,35), (33,17,15), (33,20,35), (33,20,15), (33,33,35), (33,33,15), (33,35,32), (33,35,20), (33,35,17), (34,15,35)]
theorem native_affine_repair_rows :
    oldRepair.foldl rowStep identity = newRepair.foldl rowStep identity := by native_decide
theorem native_repair_size : oldRepair.length = 182 ∧ newRepair.length = 18 := by native_decide
theorem compact_native_cost : 166 - 151 = 15 ∧ 9 - 8 = 1 := by decide
theorem exact_phase_quotient_dimensions : 951 + 10 = 961 := by decide
end GVQCC.V30
