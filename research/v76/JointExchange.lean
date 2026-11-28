import Mathlib

/-- Joint nonlinear chart exchange across a measurement boundary.
The hypotheses are equalities on the reachable domain. The theorem does
not certify that either hypothesis holds in a particular physical circuit. -/
theorem joint_delta
    (f0 f1 g0 g1 w v : Bool)
    (hf : v = Bool.xor f0 (w && f1))
    (hg : w = Bool.xor g0 (v && g1)) :
    Bool.xor w v = Bool.xor f0 ((!f1) && (Bool.xor g0 (f0 && g1))) := by
  cases f0 <;> cases f1 <;> cases g0 <;> cases g1 <;>
    cases w <;> cases v <;> simp_all [Bool.xor]

/-- Discrete Leibniz identity in GF(2), including the quadratic cross term. -/
theorem product_delta
    (a b da db : Bool) :
    Bool.xor (Bool.xor a da && Bool.xor b db) (a && b) =
      Bool.xor (Bool.xor (a && db) (b && da)) (da && db) := by
  cases a <;> cases b <;> cases da <;> cases db <;> decide
