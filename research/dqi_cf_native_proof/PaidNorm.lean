import NativeProof
namespace GVQCC.PaidNorm
open GVQCC.CFNative
set_option maxRecDepth 100000
set_option maxHeartbeats 0

-- Independent binary polynomial field model, with explicit monic modulus.
def mulLoop (cap modulus : Nat) : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, z => z
  | n+1, a, b, z =>
    let d := 2*a
    mulLoop cap modulus n (if d ≥ cap then Nat.xor d modulus else d)
      (b/2) (if b%2 == 1 then Nat.xor z a else z)
def m4 (a b : Nat) := mulLoop 4 7 2 a b 0
def m64 (a b : Nat) := mulLoop 64 67 6 a b 0
def p64 (x : Nat) : Nat → Nat
  | 0 => 1
  | n+1 => m64 x (p64 x n)
def tx (a b : Nat) := Nat.xor a b
def pack (a b c : Nat) := tx a (tx (4*b) (16*c))
def comp (x : Nat) := (x%4, x/4%4, x/16)
-- [1, lambda, z, lambda*z, z², lambda*z²] in the GF64 polynomial basis.
def basis : List Nat := [1,59,6,28,20,11]
def embed (x : Nat) := (List.range 6).foldl
  (fun v i => if Nat.testBit x i then tx v (basis[i]!) else v) 0
def cof (x : Nat) : Nat :=
  let (a,b,c) := comp x
  pack (tx (m4 a a) (m4 2 (m4 b c)))
       (tx (m4 2 (m4 c c)) (m4 a b))
       (tx (m4 b b) (m4 a c))
def cube (a : Nat) := if a == 0 then 0 else 1
def norm (x : Nat) :=
  let (a,b,c) := comp x
  tx (m4 2 (m4 b ((cof x)/16))) (tx (cube a) (m4 3 (cube c)))
def inv (x : Nat) :=
  let (a,b,c) := comp (cof x)
  let n := m4 (norm x) (norm x)
  pack (m4 a n) (m4 b n) (m4 c n)
def rowCheck (x : Nat) : Bool :=
  let q := embed x
  (embed (cof x) == m64 (p64 q 4) (p64 q 16)) &&
  (embed (norm x) == p64 q 21) &&
  ((norm x == 0) == (x == 0)) &&
  (embed (inv x) == (if q == 0 then 0 else p64 q 62)) &&
  (m64 q (embed (inv x)) == (if q == 0 then 0 else 1))

theorem basis_injective_check : ((List.range 64).map embed).eraseDups.length = 64 := by decide
theorem cube4_check : ((List.range 4).all (fun a =>
    m4 a (m4 a a) == cube a)) = true := by decide
theorem all64_cofactor_norm_inverse : ((List.range 64).all rowCheck) = true := by decide
theorem exact_inverse_row (x : Nat) (hx : x < 64) : rowCheck x = true := by
  exact List.all_eq_true.mp all64_cofactor_norm_inverse x (List.mem_range.mpr hx)

def codes6 : List Nat :=
[846,974,62149,324,714,848,70341,323,713,783,66245,64,454,1104,70081,68,458,848,912,70081,66,456,782,846,61889,322,324,712,714,782,974,62149,256,258,646,648,783,1103,66180,259,649,849,74372,258,648,973,57988,67,68,457,458,976,70081,256,258,646,648,784,70276,66,68,456,458,848,912,976,70081,2,3,5,710,712,713,785,74432,192,193,711,713,844,972,53955,192,193,66,258,322,67,259,323,68,5,710,711,456,648,457,649,713,458,782,785,844,846,972,973,974,1103]
def gates6 := codes6.map decode
def spec6 : List Poly :=
  (List.range 18).map (fun w =>
    if w < 12 then [[w]] else
      [w] :: ((List.range 6).flatMap (fun i =>
        (List.range 6).filterMap (fun j =>
          if Nat.testBit (m64 (2^i) (2^j)) (w-12) then some [i,j+6] else none))))
theorem gateCount6 : gates6.length = 108 := by decide
theorem paidCount6 : (gates6.filter (fun g => match g with | .ccx _ _ _ => true | _ => false)).length = 15 := by decide
theorem symbolic6 : symRun gates6 (initial 18) = spec6 := by decide
theorem allInputs6 (v : Nat → Bool) :
    bitRun gates6 ((initial 18).map (pe v)) = spec6.map (pe v) := by
  rw [← evalRun, symbolic6]

-- HMR norm repayment is linear in the classical mask; the cube term
-- can be repaid with two Z_IF and one CZ_IF, without another CCX.
def cubeBit (a b : Bool) := bx (bx a b) (a && b)
theorem cubeBit_or (a b : Bool) : cubeBit a b = (a || b) := by
  cases a <;> cases b <;> decide
theorem cubeHmr (a b m : Bool) :
    bx (m && cubeBit a b) (bx (m && a) (bx (m && b) (m && (a && b)))) = false := by
  cases a <;> cases b <;> cases m <;> decide
theorem normHmr (a b c m : Bool) :
    bx (m && bx a (bx b c)) (bx (m && a) (bx (m && b) (m && c))) = false := by
  cases a <;> cases b <;> cases c <;> cases m <;> decide

#print axioms basis_injective_check
#print axioms cube4_check
#print axioms all64_cofactor_norm_inverse
#print axioms exact_inverse_row
#print axioms gateCount6
#print axioms paidCount6
#print axioms symbolic6
#print axioms allInputs6
#print axioms cubeBit_or
#print axioms cubeHmr
#print axioms normHmr
end GVQCC.PaidNorm
