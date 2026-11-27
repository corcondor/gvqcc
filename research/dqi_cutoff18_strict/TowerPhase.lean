import Mathlib
namespace GVQCC.V129
open scoped BigOperators
variable {F : Type*} [CommRing F]

/-- Exact Karatsuba phase in the quotient Y²+Y+K, characteristic two. -/
theorem quadratic_phase (a b c d K m n : F) (h : (2:F)=0) :
    m*(a*c+K*b*d)+n*(a*d+b*c+b*d) =
      (m+n)*a*c+(m*K)*b*d+n*(a+b)*(c+d) := by
  symm
  calc
    _ = m*(a*c+K*b*d)+n*(a*d+b*c+b*d)+2*n*a*c := by ring
    _ = _ := by rw [h,zero_mul,zero_mul,zero_mul,add_zero]

/-- The classical mask of a multiplication is a Hankel anti-diagonal. -/
theorem diagonal_mask (L : F →+ ZMod 2) (t : F) (i j : ℕ) :
    L (t^i*t^j) = L (t^(i+j)) := by rw [pow_add]

/-- Multiplication basis modulus X^12+X^6+X^4+X+1. -/
theorem mask_recurrence (L : F →+ ZMod 2) (t : F) (i : ℕ)
    (ht : t^12=t^6+t^4+t+1) :
    L (t^(12+i)) = L (t^(6+i))+L (t^(4+i))+L (t^(1+i))+L (t^i) := by
  have h : t^(12+i)=t^(6+i)+t^(4+i)+t^(1+i)+t^i := by
    rw [pow_add t 12 i,ht]
    simp only [pow_add, pow_one]
    ring
  rw [h,map_add,map_add,map_add]

/-- Sharing a classical XOR mask across commuting diagonal gates. -/
theorem pool_mask {I : Type*} (s : Finset I) (m : I → ZMod 2) (p : ZMod 2) :
    ∑ i ∈ s, m i*p = (∑ i ∈ s, m i)*p := by
  rw [Finset.sum_mul]

theorem reuse_mask (a b p q : ZMod 2) :
    a*p+b*p+a*q+b*q=(a+b)*p+(a+b)*q := by ring

theorem duplicate_phase (a : ZMod 2) : a+a=0 := by
  have h : (2:ZMod 2)=0 := by decide
  calc a+a=2*a := by ring
       _=0 := by rw [h,zero_mul]

theorem guarded_phase (a b m n : Bool) :
    Bool.xor (m && a && b) (n && a && b) =
      (Bool.xor m n && a && b) := by
  cases a <;> cases b <;> cases m <;> cases n <;> decide

-- Concrete smallest improving block: 2 x 2 truncated product over GF(4096).
set_option maxRecDepth 100000
set_option maxHeartbeats 0
def terms : List (Nat × Nat × Nat) := [(5870896,10683488,405702),(13880320,12044025,10327009),(9066800,1360537,10199847),(8569721,6757602,4614348),(252591,12048122,6179784),(8460758,13683224,1581828),(3245080,11912888,1901472),(7368282,6114216,1413810),(4319810,15240464,561426),(16379333,7462458,6118314),(10053284,6118315,14043803),(6327137,2917777,9113905),(7064455,1495771,14216015),(2276236,3048912,754032),(4812811,3692299,13855295),(4749911,14481034,5275401),(13568919,1454525,12573780),(8876480,13289271,15704925),(1027505,13714968,1577603),(6816898,15971794,4902388),(6793523,2290634,5431159),(4265771,3486306,4660371),(1164867,10423968,352506),(5296488,11156674,4357225),(16691969,3703536,1011993),(8323596,8030927,15757658),(8499469,4327487,16711747),(6384126,802951,14840378),(12149991,6360032,508036),(14159129,7162727,15053502),(6530788,4857868,3208263),(5815824,14334597,10710370),(3873012,9476745,9672997),(1683582,14892116,2800889),(15652321,5169038,7359317),(16213407,11396058,5961644),(7622948,3776842,5477775),(10414303,9590642,5216875),(15383035,11269688,1839076),(4924874,9485586,4840753),(8288896,406137,10271836),(3497802,9867115,13984109),(16327201,15197261,11552767),(3224400,7705764,2464128),(13111665,9597161,9821823),(1360181,9442022,6731808),(10686163,8015297,8462933),(12046310,15359783,15178357),(6756850,13919918,7652917),(12050018,5012646,6606341),(13682576,9968136,1050672),(11912231,11744656,625907),(6111882,6525562,6253033),(15238829,13674474,5694746),(6116110,16204248,1831654),(2916360,5612317,12223929),(7459590,10674885,10581855),(1497968,1381905,9099395),(3050441,7051924,2742777),(3690681,8293509,10682746),(10711483,4641128,1493829),(11004533,247595,14119884),(302030,4527683,12695689),(13822989,12500504,1576260),(6459381,920562,5152881),(11559928,11580906,5680437),(7034747,8206398,8232065),(14080382,4206256,869398),(12422661,4003470,7395479),(11586885,8738638,7559808),(11443270,5104233,9738155),(1986819,13153575,15191339),(11184437,3548559,15893625),(12669171,11946546,5055078),(7076294,8417213,12559903),(6699260,3105666,4228841),(6227426,7917679,16071480),(3751198,5747693,11910609),(7217003,2893026,4617248),(12401938,895194,5907875),(13836921,2198584,1855875),(15744088,6982884,2589010),(16766219,1985464,1946227),(1042771,7653212,3814177),(8115463,6933380,2192283),(12252118,7025421,11709672),(12658385,194697,9690995),(2832822,3184595,13113632),(7598736,1090562,4285721),(5819174,2110417,9010233),(11829745,87300,2099873),(6404291,16317271,15306541),(13973810,16363091,13206924),(13579298,5234350,7658455),(1009481,598662,6333574),(12604267,4652072,1343313),(9415955,4063180,3346316),(9047609,10056298,5721772),(369450,10784166,6570272),(5263426,7566438,6807290),(7434672,6859707,14574855),(2171378,1826781,12172285),(3427243,13464345,10104454),(2876817,14605126,6503260),(2076218,1288287,16324058)]

def mulLoop : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, z => z
  | n+1,a,b,z =>
    let d := 2*a
    mulLoop n (if d ≥ 4096 then Nat.xor d 4179 else d) (b/2)
      (if b%2==1 then Nat.xor z a else z)

def fieldMul (a b : Nat) := mulLoop 12 a b 0
def coeff (i j : Nat) :=
  if i/12+j/12 < 2 then fieldMul (2^(i%12)) (2^(j%12)) * 2^(12*(i/12+j/12)) else 0
def emittedCoeff (i j : Nat) :=
  terms.foldl (fun acc t => if Nat.testBit t.1 i && Nat.testBit t.2.1 j
    then Nat.xor acc t.2.2 else acc) 0
def rowOK (i : Nat) := (List.range 24).all (fun j => emittedCoeff i j == coeff i j)

theorem rank105 : terms.length=105 := by decide
theorem rowcheck : (List.range 24).all rowOK = true := by decide
theorem coefficient_exact (i j : Nat) (hi : i<24) (hj : j<24) :
    emittedCoeff i j = coeff i j := by
  have h := List.all_eq_true.mp rowcheck i (List.mem_range.mpr hi)
  exact beq_iff_eq.mp (List.all_eq_true.mp h j (List.mem_range.mpr hj))

end GVQCC.V129
#print axioms GVQCC.V129.quadratic_phase
#print axioms GVQCC.V129.diagonal_mask
#print axioms GVQCC.V129.mask_recurrence
#print axioms GVQCC.V129.pool_mask
#print axioms GVQCC.V129.reuse_mask
#print axioms GVQCC.V129.duplicate_phase
#print axioms GVQCC.V129.guarded_phase
#print axioms GVQCC.V129.rank105
#print axioms GVQCC.V129.rowcheck
#print axioms GVQCC.V129.coefficient_exact
