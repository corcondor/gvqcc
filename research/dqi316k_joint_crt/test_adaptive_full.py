import test_repaired247 as t
import numpy as np
z=np.load('adaptive_stress.npz')
def generate():
    return [(str(l),seed,z['S'][ix],z['M'][ix],z['weights'][ix],z['expected'][ix]) for l in np.unique(z['labels']) for ix in [z['labels']==l] for seed in [821,822]]
t.generate=generate
t.main()
