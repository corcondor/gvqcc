import Std

namespace GVQCC.CFJoint
set_option maxRecDepth 100000
set_option maxHeartbeats 0

/-- The exact mixed correction term of a changed CCX control pair. -/
theorem ccx_difference (a b da db : Bool) :
    Bool.xor ((Bool.xor a da) && (Bool.xor b db)) (a && b) =
      Bool.xor (Bool.xor (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide

/-- The cross term of two successive linear updates must not be lost. -/
theorem paired_cross (a b c g h : Bool) :
    Bool.xor c (h && Bool.xor a (g && b)) =
      Bool.xor (Bool.xor c (h && a)) ((h && g) && b) := by
  cases a <;> cases b <;> cases c <;> cases g <;> cases h <;> decide

/-- Dirty-target update followed by its inverse. -/
theorem dirty_involution (z a b : Bool) :
    Bool.xor (Bool.xor z (a && b)) (a && b) = z := by
  cases z <;> cases a <;> cases b <;> decide

/-- HMR correction is valid when the exact Boolean carrier is transported. -/
theorem phase_transport (m p f g : Bool) (h : f = g) :
    Bool.xor (Bool.xor p (m && f)) (m && g) = p := by
  rw [← h]
  exact dirty_involution p m f

/-- Rank-one accumulation; all coefficients are interpreted over GF(2). -/
def tensorEval (n : Nat) (c : Nat → Nat → Bool) (a b : Nat → Bool) : Bool :=
  (List.range n).foldl (fun z i =>
    (List.range n).foldl (fun w j => Bool.xor w (c i j && a i && b j)) z) false

theorem tensor_refinement (n : Nat) (c d : Nat → Nat → Bool)
    (a b : Nat → Bool) (h : ∀ i j, c i j = d i j) :
    tensorEval n c a b = tensorEval n d a b := by
  have he : c = d := funext (fun i => funext (fun j => h i j))
  rw [he]

/-- Independent bit-serial field multiplication, modulus 0x1053. -/
def gfLoop : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, z => z
  | n+1, a, b, z =>
    let d := a * 2
    gfLoop n (if d ≥ 4096 then Nat.xor d 4179 else d) (b / 2)
      (if b % 2 == 1 then Nat.xor z a else z)

def gf12 (a b : Nat) : Nat := gfLoop 12 a b 0

def gf24 (k x y : Nat) : Nat :=
  let a := x % 4096
  let b := x / 4096
  let c := y % 4096
  let d := y / 4096
  let ac := gf12 a c
  let bd := gf12 b d
  Nat.xor ac (gf12 k bd) +
    4096 * (Nat.xor (Nat.xor (gf12 a d) (gf12 b c)) bd)

def coeff (ts : List (Nat × Nat)) (i j : Nat) : Nat :=
  ts.foldl (fun z t =>
    if Nat.testBit t.1 i && Nat.testBit t.1 j then Nat.xor z t.2 else z) 0

def basisCheck (n : Nat) (ref : Nat → Nat → Nat) (ts : List (Nat × Nat)) : Bool :=
  (List.range n).all (fun i =>
    (List.range n).all (fun j => coeff ts i j == ref (2^i) (2^j)))

def terms42 : List (Nat × Nat) :=
[(321,1468),(272,2801),(2016,3418),(81,3917),(1697,1963),(1776,535),(3855,2329),(592,879),(608,1629),(3423,2678),(3439,1330),(48,3115),(3879,2843),(2162,3297),(156,3592),(1877,2042),(4027,745),(2286,2546),(2617,590),(2282,1283),(1636,382),(723,1869),(3165,1149),(3726,1587),(393,874),(820,2896),(510,3123),(701,2106),(119,1891),(714,1033),(3943,412),(2300,3971),(3982,2115),(1947,3615),(233,1984),(1906,1628),(2088,1070),(3056,415),(160,2936),(984,1457),(2184,2791),(2896,3785)]

def terms99 : List (Nat × Nat) :=
[(13098109,10846208),(4523088,3727360),(8575021,10313728),(6792826,12607488),(1024250,6692864),(6817408,10895360),(10516999,245760),(4891818,16285696),(15392429,16465920),(3197,10848856),(1104,3728270),(2093,10316246),(1658,12610566),(250,6694498),(1664,10898020),(2567,245820),(1194,16289672),(3757,16469940),(2487985,3326524),(7017710,2343184),(5169759,1114924),(5303440,9513269),(13175198,9654311),(10085646,162066),(7674401,3193646),(10624368,11724837),(14092113,8540939),(5170865,3326224),(2487534,2343724),(7017055,1114684),(10087568,9510951),(5302686,9656594),(13174030,162101),(14092833,3192869),(7675248,11723531),(10622801,8543022),(6238121,7206837),(7677504,6343407),(2755049,867674),(13669024,1484300),(3876338,13512915),(15447890,14194399),(9420041,11886954),(5112754,7761123),(12697275,12782985),(10862505,7205226),(1123904,6343907),(11835881,867721),(16421536,1484646),(6555122,13515824),(10393426,14195542),(6237449,11889212),(7676850,7760773),(2756283,12779961),(10913125,2010270),(7632638,16012180),(13824923,15400714),(1808458,2301243),(15420566,2617056),(15783132,324571),(12393775,1728325),(10435176,14110383),(2238279,13439466),(15783269,2010484),(1808126,16014545),(15418267,15397285),(10434634,2301706),(2239638,2616478),(12391644,324500),(7335215,1728224),(3783272,14107611),(5658439,13442363),(14765435,2944011),(1539286,16028940),(16134573,14186759),(13459674,6613961),(1757720,1622850),(14136002,8136843),(2895265,5293184),(896718,9469637),(2196335,12630597),(3603835,2944709),(14294230,16030277),(15524269,14185600),(12632282,6614407),(3887640,1622734),(16487106,8138569),(16137633,5292428),(14765774,9467842),(1536879,12629582),(3579904,1590),(8790016,3791),(11567104,2297),(14409728,288),(6840320,3980),(11763712,3756),(15548416,2202),(15613952,4079),(196608,1909)]

theorem rank42_count : terms42.length = 42 := by decide
theorem rank99_count : terms99.length = 99 := by decide
theorem field42_coefficients : basisCheck 12 gf12 terms42 = true := by native_decide
theorem residue3257_coefficients : basisCheck 24 (gf24 3257) terms99 = true := by native_decide

#print axioms ccx_difference
#print axioms paired_cross
#print axioms dirty_involution
#print axioms phase_transport
#print axioms tensor_refinement
#print axioms rank42_count
#print axioms rank99_count
#print axioms field42_coefficients
#print axioms residue3257_coefficients

end GVQCC.CFJoint
