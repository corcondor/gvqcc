import Init
namespace GVQCC.V117
set_option maxRecDepth 100000
set_option maxHeartbeats 0
def bx (a b : Bool) := Bool.xor a b
def parity (n : Nat) : Bool :=
  (List.range 12).foldl (fun s i => bx s (n.testBit i)) false
def xtime (a : Nat) : Nat :=
  if a.testBit 11 then Nat.xor (2*a) 0x1053 else 2*a
def gfMul (a b : Nat) : Nat :=
  ((List.range 12).foldl (fun (p : Nat × Nat) i =>
    (xtime p.1, if b.testBit i then Nat.xor p.2 p.1 else p.2)) (a,0)).2
def terms : List (Nat × Nat) := [(3617,2844),(2656,1033),(1089,3861),(2232,693),(2320,192),(424,629),(1689,2409),(880,1724),(1513,4053),(2695,3560),(3656,2111),(1231,1495),(1720,806),(2984,128),(3344,934),(3135,3662),(1504,2841),(2527,1367),(3841,3916),(2876,3289),(1085,917),(3342,2208),(688,499),(4030,2387),(527,1567),(2444,1145),(2947,614),(2983,1335),(3860,1885),(1203,618),(782,2354),(8,501),(774,2247),(2217,3568),(3868,3695),(1973,927),(3708,2066),(920,3705),(3556,1643),(544,384),(3856,1258),(3376,1386),(3164,3448),(3208,4089),(212,641)]
def tower (a b : Nat) : Nat :=
  terms.foldl (fun r (m,c) =>
    if parity (Nat.land a m) && parity (Nat.land b m) then Nat.xor r c else r) 0
-- Finite basis certificate for the complete 12x12 multiplication tensor.
-- Bilinearity and serialized circuit ANF are checked separately.
theorem gf45_basis : ∀ (i j : Fin 12),
    tower (2^i.val) (2^j.val) = gfMul (2^i.val) (2^j.val) := by decide
theorem xor_add_product (a b c : Bool) :
    (bx a b && c) = bx (a && c) (b && c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem shear_inverse (p s t : Bool) :
    bx (bx t (p && s)) (p && s) = t := by
  cases p <;> cases s <;> cases t <;> decide
theorem dirty_hub (a b h x : Bool) :
    bx (bx x h) (bx h (a && b)) = bx x (a && b) := by
  cases a <;> cases b <;> cases h <;> cases x <;> decide
-- A reversible exchange: encoded bit24 replaces v5, with v4 and bit23 retained.
theorem word24_exchange (v5 v4 w23 : Bool) :
    let w24 := !(bx v5 (w23 && v4))
    !(bx w24 (w23 && v4)) = v5 := by
  cases v5 <;> cases v4 <;> cases w23 <;> decide
theorem word24_from_sign (v5 v4 w23 : Bool) :
    !(bx (bx v5 v4) ((!w23) && v4)) = !(bx v5 (w23 && v4)) := by
  cases v5 <;> cases v4 <;> cases w23 <;> decide
end GVQCC.V117
#print axioms GVQCC.V117.gf45_basis
#print axioms GVQCC.V117.xor_add_product
#print axioms GVQCC.V117.shear_inverse
#print axioms GVQCC.V117.dirty_hub
#print axioms GVQCC.V117.word24_exchange
#print axioms GVQCC.V117.word24_from_sign
