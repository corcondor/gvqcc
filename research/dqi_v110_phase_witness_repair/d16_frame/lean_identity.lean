import Std

namespace GVQCC.D16Frame
def plus (x y : Bool) := Bool.xor x y
def translate {A : Type} (x d : A → Bool) (i : A) := plus (x i) (d i)
def shear {A B : Type} (F : (A → Bool) → B → Bool)
    (u : A → Bool) (v : B → Bool) : B → Bool :=
  translate v (F u)
theorem rearrange (x a b c : Bool) :
    plus (plus (plus x a) b) c = plus (plus x b) (plus a c) := by
  cases x <;> cases a <;> cases b <;> cases c <;> decide
theorem conjugation {A B : Type} (F : (A → Bool) → B → Bool)
    (h : ∀ (u d : A → Bool) (i : B), F (translate u d) i = plus (F u i) (F d i))
    (u d : A → Bool) (v e : B → Bool) (i : B) :
    shear F (translate u d) (translate (shear F u v) e) i =
      plus (plus (v i) (e i)) (F d i) := by
  unfold shear translate
  change plus (plus (plus (v i) (F u i)) (e i)) (F (translate u d) i) = _
  rw [h]
  generalize hv : v i = x
  generalize he : e i = a
  generalize hu : F u i = b
  generalize hd : F d i = c
  cases x <;> cases a <;> cases b <;> cases c <;> decide
end GVQCC.D16Frame
#print axioms GVQCC.D16Frame.conjugation

namespace GVQCC.D16Frame

def parity (a x : Nat) : Bool :=
  (List.range 6).foldl (fun p i => plus p (a.testBit i && x.testBit i)) false

def polarPoly (p x : Nat) : Bool :=
  let pairs := (List.range 6).flatMap (fun i =>
    ((List.range 6).filter (fun j => i < j)).map (fun j => (i,j)))
  (pairs.zipIdx).foldl
    (fun z ((i,j),k) => plus z (p.testBit k && x.testBit i && x.testBit j)) false

def evaluate (products : List (Nat × Nat)) (sel a x : Nat) : Bool :=
  ((products.zipIdx).foldl
    (fun z ((u,v),i) => plus z (sel.testBit i && parity u x && parity v x))
    (parity a x))

def agrees (products : List (Nat × Nat)) (rows : List (Nat × Nat × Nat)) : Bool :=
  (List.range 64).all (fun x => rows.all (fun (p,sel,a) =>
    polarPoly p x == evaluate products sel a x))

theorem W70_witness : agrees [(1,2),(4,8),(16,32),(29,38),(31,37)]
    [(462,24,1),(513,3,0),(11506,15,4),(16385,5,0)] = true := by decide

theorem W84_witness : agrees [(1,2),(4,8),(6,11),(16,32),(21,42),(26,47)]
    [(99,6,2),(513,3,0),(6324,27,0),(11544,48,10),(16385,9,0)] = true := by decide

end GVQCC.D16Frame
#print axioms GVQCC.D16Frame.W70_witness
#print axioms GVQCC.D16Frame.W84_witness
