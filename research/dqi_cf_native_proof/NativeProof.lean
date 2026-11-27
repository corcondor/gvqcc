import Std

namespace GVQCC.CFNative
set_option maxRecDepth 100000
set_option maxHeartbeats 0

def bx (a b : Bool) := Bool.xor a b

theorem xx (a b : Bool) : bx a (bx a b) = b := by
  cases a <;> cases b <;> decide
theorem xswap (a b c : Bool) : bx a (bx b c) = bx b (bx a c) := by
  cases a <;> cases b <;> cases c <;> decide
theorem andAssoc (a b c : Bool) : ((a && b) && c) = (a && (b && c)) := by
  cases a <;> cases b <;> cases c <;> decide

abbrev Mon := List Nat
abbrev Poly := List Mon
def me (v : Nat → Bool) : Mon → Bool
  | [] => true
  | i :: is => v i && me v is
def pe (v : Nat → Bool) : Poly → Bool
  | [] => false
  | m :: ms => bx (me v m) (pe v ms)
def key (a : Mon) : Nat := a.foldl (fun n i => 256*n+i+1) 0
def toggle (a : Mon) : Poly → Poly
  | [] => [a]
  | b :: bs => if a = b then bs else if key a < key b then a :: b :: bs else b :: toggle a bs

theorem evalToggle (v : Nat → Bool) (a : Mon) (p : Poly) :
    pe v (toggle a p) = bx (me v a) (pe v p) := by
  induction p with
  | nil => rfl
  | cons b bs ih =>
    by_cases h : a = b
    · subst b
      simp only [toggle, pe]
      exact (xx (me v a) (pe v bs)).symm
    · by_cases h' : key a < key b
      · simp only [toggle, ite_eq_right h, ite_eq_left h', pe]
      · simp only [toggle, ite_eq_right h, ite_eq_right h', pe, ih]
        exact xswap (me v b) (me v a) (pe v bs)

def addP (p : Poly) : Poly → Poly
  | [] => p
  | a :: as => toggle a (addP p as)

theorem evalAdd (v : Nat → Bool) (p q : Poly) :
    pe v (addP p q) = bx (pe v p) (pe v q) := by
  induction q with
  | nil =>
    change pe v p = bx (pe v p) false
    cases pe v p <;> rfl
  | cons a as ih =>
    simp only [addP, evalToggle, ih, pe]
    exact xswap (me v a) (pe v p) (pe v as)

theorem evalAppend (v : Nat → Bool) (a b : Mon) :
    me v (a ++ b) = (me v a && me v b) := by
  induction a with
  | nil => rfl
  | cons i is ih =>
    simp only [List.cons_append, me, ih]
    exact (andAssoc (v i) (me v is) (me v b)).symm

theorem evalPrefix (v : Nat → Bool) (a : Mon) (q : Poly) :
    pe v (q.map (fun b => a ++ b)) = (me v a && pe v q) := by
  induction q with
  | nil =>
    change false = (me v a && false)
    cases me v a <;> rfl
  | cons b bs ih =>
    simp only [List.map_cons, pe, evalAppend, ih]
    cases me v a <;> cases me v b <;> cases pe v bs <;> rfl

def mulP (p q : Poly) : Poly :=
  match p with
  | [] => []
  | a :: as => addP (mulP as q) (q.map (fun b => a ++ b))

theorem evalMul (v : Nat → Bool) (p q : Poly) :
    pe v (mulP p q) = (pe v p && pe v q) := by
  induction p with
  | nil => rfl
  | cons a as ih =>
    simp only [mulP, evalAdd, ih, evalPrefix, pe]
    cases me v a <;> cases pe v as <;> cases pe v q <;> rfl

def readAt (d : α) : List α → Nat → α
  | [], _ => d
  | a :: _, 0 => a
  | _ :: as, i+1 => readAt d as i
def writeAt : List α → Nat → α → List α
  | [], _, _ => []
  | _ :: as, 0, x => x :: as
  | a :: as, i+1, x => a :: writeAt as i x

theorem readMap (f : α → β) (d : α) (s : List α) (i : Nat) :
    readAt (f d) (s.map f) i = f (readAt d s i) := by
  induction s generalizing i <;> cases i <;> simp [readAt, *]
theorem writeMap (f : α → β) (s : List α) (i : Nat) (x : α) :
    (writeAt s i x).map f = writeAt (s.map f) i (f x) := by
  induction s generalizing i <;> cases i <;> simp [writeAt, *]

inductive Gate where
  | cx (a t : Nat)
  | ccx (a b t : Nat)
  deriving DecidableEq

def symStep (g : Gate) (s : List Poly) : List Poly :=
  match g with
  | .cx a t => writeAt s t (addP (readAt [] s t) (readAt [] s a))
  | .ccx a b t => writeAt s t (addP (readAt [] s t) (mulP (readAt [] s a) (readAt [] s b)))
def bitStep (g : Gate) (s : List Bool) : List Bool :=
  match g with
  | .cx a t => writeAt s t (bx (readAt false s t) (readAt false s a))
  | .ccx a b t => writeAt s t (bx (readAt false s t) (readAt false s a && readAt false s b))

theorem evalStep (v : Nat → Bool) (g : Gate) (s : List Poly) :
    (symStep g s).map (pe v) = bitStep g (s.map (pe v)) := by
  have h (i : Nat) : pe v (readAt [] s i) = readAt false (s.map (pe v)) i :=
    (readMap (pe v) [] s i).symm
  cases g with
  | cx a t => simp only [symStep, bitStep, writeMap, evalAdd, h]
  | ccx a b t => simp only [symStep, bitStep, writeMap, evalAdd, evalMul, h]

def symRun : List Gate → List Poly → List Poly
  | [], s => s
  | g :: gs, s => symRun gs (symStep g s)
def bitRun : List Gate → List Bool → List Bool
  | [], s => s
  | g :: gs, s => bitRun gs (bitStep g s)

theorem evalRun (v : Nat → Bool) (gs : List Gate) (s : List Poly) :
    (symRun gs s).map (pe v) = bitRun gs (s.map (pe v)) := by
  induction gs generalizing s with
  | nil => rfl
  | cons g gs ih =>
    simp only [symRun, bitRun, ih, evalStep]

def initial (n : Nat) : List Poly := (List.range n).map (fun i => [[i]])

def gfLoop : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, z => z
  | n+1, a, b, z =>
    let d := a * 2
    gfLoop n (if d ≥ 4096 then Nat.xor d 4179 else d) (b / 2)
      (if b % 2 == 1 then Nat.xor z a else z)
def gf12 (a b : Nat) : Nat := gfLoop 12 a b 0

-- The exact serialized GF12 42-CCX 510-op gate stream, encoded a+64*b+4096*(t+1)
-- for CCX and a+64*t for CX. Independently derive the specification from GF(4096).
def codes : List Nat :=
[261,1041,1624,1752,1880,2200,2264,103428,453,1233,1760,1824,1888,1952,2144,2272,136391,707,709,1487,1489,1634,1698,1762,1890,144843,711,1491,1566,1630,1886,2014,2142,2206,128459,261,264,1041,1044,1626,1818,1946,111620,512,518,1292,1298,1563,1947,2075,2267,115976,516,1296,1691,115976,8,9,788,789,1564,1628,2076,2204,119552,7,10,787,790,1825,2081,2273,140032,4,784,1761,140032,4,8,784,788,1697,140032,389,393,1169,1173,1626,2010,2202,2266,111750,259,262,267,1039,1042,1047,1952,136196,263,1043,2206,128004,267,1047,2208,136196,580,584,1360,1364,1570,1826,2274,144713,642,646,1422,1426,1568,1632,1760,2144,136586,449,451,454,1229,1231,1234,1561,1881,2265,107719,513,514,517,1293,1294,1297,2201,107784,456,1236,1630,1694,1758,2014,2270,128199,457,1237,2206,128199,584,1364,1945,107849,259,261,262,263,264,1039,1041,1042,1043,1044,1763,148484,450,452,458,459,1230,1232,1238,1239,1564,1692,120007,391,1171,1564,119942,579,583,584,1295,1299,1301,2272,136457,649,1428,1689,1753,1881,107914,266,1046,2265,107524,265,266,1296,1302,2073,107780,138,1422,2008,2072,2200,103810,323,327,1231,1233,1822,1886,2078,2206,128197,256,259,262,1292,1295,1298,1571,1891,2019,148740,1,2,7,8,9,972,973,981,982,1566,127936,128,982,1763,1955,2019,2147,2211,148418,5,979,982,2264,103360,322,982,1944,103365,512,513,1166,1168,1169,1172,1825,2081,2209,140424,516,1298,1692,1884,1948,2268,120072,67,71,74,75,909,913,915,918,919,2140,119681,68,1294,1298,1691,1883,2011,2075,115969,513,914,2139,115592,2,4,6,10,11,1041,1042,1043,1047,1688,1944,2008,2072,2200,2264,103424,128,256,384,448,129,66,129,1,321,513,577,641,2,258,514,578,3,67,131,259,323,515,579,707,132,324,388,452,516,580,453,327,453,5,261,645,454,391,454,6,134,262,326,518,582,647,458,647,7,135,711,8,9,73,265,457,521,649,713,10,74,266,458,586,714,75,139,651,1036,1164,1228,909,973,1037,1229,1357,1421,1038,1230,1294,1358,1422,1167,978,1167,911,1231,1487,1168,1296,1360,785,1041,1425,1234,1171,1234,914,978,1042,1426,1490,1491,1239,1491,787,915,916,1428,981,1237,1301,918,982,1046,1238,1494,791,983,1303,1367,1561,1624,1561,1562,1563,1566,1568,1627,1632,1634,1635,1692,1818,1692,1688,1689,1694,1698,1699,1753,1754,1758,1760,1824,2076,1824,1818,1827,1880,1881,1882,1884,1888,1891,1944,1947,1948,1953,1955,2008,2009,2010,2017,2018,2083,2272,2083,2073,2074,2075,2076,2078,2137,2138,2142,2144,2147,2211,2274,2211,2200,2202,2203,2204,2206,2208,2209,2265,2266,2268]
def decode (c : Nat) : Gate :=
  if c / 4096 = 0 then .cx (c % 64) ((c / 64) % 64)
  else .ccx (c % 64) ((c / 64) % 64) (c / 4096 - 1)
def gates := codes.map decode
def spec : List Poly :=
  (List.range 36).map (fun w =>
    if w < 24 then [[w]] else
      [w] :: ((List.range 12).flatMap (fun i =>
        (List.range 12).filterMap (fun j =>
          if Nat.testBit (gf12 (2^i) (2^j)) (w-24) then some [i,j+12] else none))))

theorem gateCount : gates.length = 510 := by decide
theorem paidCount : (gates.filter (fun g => match g with | .ccx _ _ _ => true | _ => false)).length = 42 := by decide
theorem exactSymbolic : symRun gates (initial 36) = spec := by decide
theorem allInputs (v : Nat → Bool) :
    bitRun gates ((initial 36).map (pe v)) = spec.map (pe v) := by
  rw [← evalRun, exactSymbolic]

def sl (B C F C2 : Bool) := !B && !C2 && (C || F)
def su (B C F C2 : Bool) := !B && bx C F && C2
def cf (B C F C2 : Bool) := !B && C && F && !C2
theorem cfReuse (B C F C2 : Bool) :
    (sl B C F C2 && !(bx C F)) = cf B C F C2 := by
  cases B <;> cases C <;> cases F <;> cases C2 <;> decide
theorem cfSelector (B C F C2 : Bool) :
    bx (sl B C F C2) (cf B C F C2) = (!B && !C2 && bx C F) := by
  cases B <;> cases C <;> cases F <;> cases C2 <;> decide
theorem cfCoefficient (s h q t z : Bool) :
    bx (bx z ((h && q) && t)) (bx s h && t) =
      bx z (bx (h && q) (bx s h) && t) := by
  cases s <;> cases h <;> cases q <;> cases t <;> cases z <;> decide
theorem cfPhase (m h q s : Bool) :
    bx (m && bx (bx (h && q) s) s) (m && (h && q)) = false := by
  cases m <;> cases h <;> cases q <;> cases s <;> decide

#print axioms evalRun
#print axioms exactSymbolic
#print axioms allInputs
#print axioms gateCount
#print axioms paidCount
#print axioms cfReuse
#print axioms cfSelector
#print axioms cfCoefficient
#print axioms cfPhase

end GVQCC.CFNative
