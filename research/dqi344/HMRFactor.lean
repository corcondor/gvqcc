namespace DQI344

theorem hmr_pullback (m t f : Bool) :
    (m && Bool.xor t f) = Bool.xor (m && t) (m && f) := by
  cases m <;> cases t <;> cases f <;> decide

theorem hmr_guarded_pullback (m t f g : Bool) :
    (m && Bool.xor t (g && f)) = Bool.xor (m && t) (g && (m && f)) := by
  cases m <;> cases t <;> cases f <;> cases g <;> decide

theorem ccx_factoring (a b c t : Bool) :
    Bool.xor (Bool.xor t (a && b)) (a && c) = Bool.xor t (a && Bool.xor b c) := by
  cases a <;> cases b <;> cases c <;> cases t <;> decide

end DQI344
#print axioms DQI344.hmr_pullback
#print axioms DQI344.hmr_guarded_pullback
#print axioms DQI344.ccx_factoring
