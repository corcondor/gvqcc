import Std.Tactic

namespace V59

def bval (b : Bool) : Nat := if b then 1 else 0
def checkCell (m c : Nat) (b : Bool) : Bool :=
  if 0 < m ∧ c < m then
    let z := c + m * bval b
    let u := z % 16
    let o := Bool.xor b (decide (u ≥ m))
    decide (16 * bval o + u = z ∧ z / 2 < m ∧
      (if z ≥ m then z - m else z) = c ∧
      (decide (z ≥ m)) = b)
  else true

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem cell_all : (List.range 16).all (fun m =>
  (List.range 16).all (fun c => checkCell m c false && checkCell m c true)) = true := by decide

def tag (s : Nat) : Nat :=
  if s = 0 then 0 else if s = 1 then 1 else if s = 2 then 2 else 4 * (s - 3)

def decode (h : Bool) (y : Nat) : Nat :=
  if !h then 0 else if y % 2 = 1 then 1 else if (y / 2) % 2 = 1 then 2 else 3 + (y / 4) % 8

def checkTag (s a : Nat) : Bool :=
  if a % (2 ^ min (2*s) 5) = 0 then
    decide (decode (decide (s > 0)) (a + tag s) = s ∧ a + tag s < 32)
  else true

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem tag_all : (List.range 11).all (fun s =>
  (List.range 32).all (fun a => checkTag s a)) = true := by decide

end V59
