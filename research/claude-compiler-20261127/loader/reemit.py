# Re-emit a saved loader-0 spec and verify it exactly, forward and reverse.
# usage: reemit.py spec.json out.kmb [words.npz]
import sys, os
from common import *
sp = K.Spec.load(sys.argv[1])


def present_bank(direction):
    bk = K.Bank(0, direction=direction)
    bk.present = [True] * len(bk.present)
    bk.present_mask = sum(1 << (1 + i) for i in range(len(bk.present)))
    return bk


bk = present_bank('forward')
res = K.evaluate(sp, bk, directions='forward')
rv, _ = K.check_functions(sp, present_bank('reverse'))
print('evaluate ok', res.ok, 'toffoli', res.toffoli, 'toffoli_like', sp.toffoli_like, 'peak width', res.peak_width,
      res.violations[:5], 'reverse violations', rv[:5], flush=True)
kmb = K.emit(sp, bk, template=FAM / 'angle_k_0.kmb', check=False)
sha = K.write_kmb(kmb, sys.argv[2])
print('emitted', sys.argv[2], 'sha', sha[:16], 'ops', len(kmb.ops), flush=True)
w = K.load_words(sys.argv[3] if len(sys.argv) > 3 else None)
v = K.verify_kmb(sys.argv[2], 0, words=w, direction='forward')
print('verify forward:', v['status'], v['toffoli'], v['qubits'], flush=True)
w2 = w.copy()
w2[:, 0:5] = w[:, 0:5]
w2[:, 5:10] = 0
v2 = K.verify_kmb(sys.argv[2], 1, words=w2, direction='forward')
print('verify reverse:', v2['status'], v2['toffoli'], v2['qubits'], flush=True)
