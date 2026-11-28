import Std

namespace GVQCC.ConcreteFFT279

abbrev Word := BitVec 12

/-- Polynomial basis for the public binary field modulus X^12+X^6+X^4+X+1. -/
def xtime (a : Word) : Word :=
  (a <<< 1) ^^^ (if a.getLsbD 11 then 83 else 0)

def mulLoop : Nat → Word → Word → Word → Word
  | 0, _, _, r => r
  | n+1, a, b, r => mulLoop n (xtime a) (b >>> 1)
      (if b.getLsbD 0 then r ^^^ a else r)

def gfMul (a b : Word) : Word := mulLoop 12 a b 0

def powLoop : Nat → Nat → Word → Word → Word
  | 0, _, _, r => r
  | k+1, n, a, r => powLoop k (n/2) (gfMul a a)
      (if n%2=1 then gfMul r a else r)

def gfPow (a : Word) (n : Nat) : Word := powLoop 12 n a 1

/-- A list [p0,p1,...] denotes sum p_j X^(2^j). -/
def evalLin : List Word → Word → Word
  | [], _ => 0
  | a::as, x => gfMul a x ^^^ evalLin as (gfMul x x)

def nextLin (p : List Word) (v : Word) : List Word :=
  List.zipWith (fun a b => a ^^^ b) (p.map (gfMul v) ++ [0])
    (0 :: p.map (fun a => gfMul a a))

def polynomials : List (List Word) :=
 [[1],
  [1,1],
  [6,7,1],
  [1904,1548,381,1],
  [125,497,1391,1250,1],
  [2297,2575,3164,3843,424,1],
  [1925,3028,314,1581,676,2531,1],
  [2983,588,3686,989,2445,400,3148,1],
  [45,983,429,796,2392,1588,2265,1791,1],
  [1637,1403,2765,1841,517,1430,2260,2013,1657,1],
  [220,989,2523,827,3889,1066,3289,351,2798,1427,1],
  [1,1,1,1,1,1,1,1,1,1,1,1],
  [1,0,0,0,0,0,0,0,0,0,0,0,1]]

def pivots : List Word := [1,6,360,1232,1708,2527,1050,3231,1215,1549,1895,1]
def inverses : List Word := [1,2023,2415,1425,834,2479,430,2765,3047,1053,220,1]

def beta (k : Nat) : Word := BitVec.ofNat 12 (2^k)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem exact_recurrence :
    List.zipWith nextLin (polynomials.take 12) pivots = polynomials.drop 1 := by decide

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem exact_pivots :
    List.zipWith evalLin (polynomials.take 12) ((List.range 12).map beta) = pivots := by decide

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem exact_reciprocals :
    List.zipWith gfMul pivots inverses = List.replicate 12 1 := by decide

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem lower_basis_zeros :
    (List.range 12).all (fun k =>
      (List.range k).all (fun j => evalLin (polynomials[k]!) (beta j) == 0)) = true := by decide

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem normalized_diagonal :
    (List.range 12).all (fun k =>
      evalLin ((polynomials[k]!).map (gfMul (inverses[k]!))) (beta k) == 1) = true := by decide

/-- Exact common source-word indices in the frozen selector residual map. -/
def anchorIndices : List Nat :=
 [0,337,378,419,460,501,542,583,624,665,706,747,788,829,870,911,952,993,
 1330,1371,1412,1453,1494,1535,1576,1617,1658,1699,1740,1781,1822,1863,1904,1945,1986,2027,
 2364,2405,2446,2487,2528,2569,2610,2651,2692,2733,2774,2815,2856,2897,2938,2979,3020,3061,
 3398,3439,3480,3521,3562,3603,3644,3685,3726,3767,3808,3849,3890,3931,3972,4013,4054]

def anchorPoints : List Word :=
 [1,3628,589,1016,1503,22,880,3287,955,778,853,3268,1489,1204,1627,918,3686,619,
 487,467,225,224,2924,943,1841,3671,1603,1092,1946,3729,507,2199,2743,3633,133,365,
 2159,1545,1122,2894,493,3047,1632,3466,911,568,852,1864,3346,42,3901,2946,3169,437,
 604,729,948,3108,3773,1819,362,3521,2085,1583,2230,1074,3057,1296,349,52,306]

theorem anchor_count : anchorPoints.length = 71 ∧ anchorIndices.length = 71 := by decide
theorem distinct_anchors : anchorPoints.Nodup := by decide
theorem nonzero_anchors : (0 : Word) ∉ anchorPoints := by decide
theorem legal_anchor_indices : anchorIndices.Nodup ∧
    anchorIndices.all (fun j => j < 4095) = true := by decide

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem anchor_power_certificate :
    anchorIndices.map (gfPow 2) = anchorPoints := by decide

theorem classical_scratch_disjoint :
    691866 + 72*12 = 692730 ∧ 49140 ≤ 691866 := by decide

#print axioms exact_recurrence
#print axioms exact_pivots
#print axioms exact_reciprocals
#print axioms lower_basis_zeros
#print axioms normalized_diagonal
#print axioms anchor_count
#print axioms distinct_anchors
#print axioms nonzero_anchors
#print axioms legal_anchor_indices
#print axioms anchor_power_certificate
#print axioms classical_scratch_disjoint
end GVQCC.ConcreteFFT279
