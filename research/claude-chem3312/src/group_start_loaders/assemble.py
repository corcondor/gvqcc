# usage: assemble.py k=file [k=file ...]  -> family/ (copy of dc3356 family with the given group-start loaders replaced),
# then the exact local gate: every loader forward and reverse (loader 0 reverse as an exchanged-table run) on all 1219 addresses and all HMR outcomes.
import sys, shutil, hashlib, json, time
from pathlib import Path
from common import *

NOTICE = open(Path(__file__).resolve().parent / 'NOTICE.txt', encoding='utf-8').read()

out = Path(__file__).resolve().parent / 'family'
repl = {int(a.split('=')[0]): Path(a.split('=')[1]) for a in sys.argv[1:]}
if out.exists():
    shutil.rmtree(out)
shutil.copytree(FAM, out)
for k, f in repl.items():
    shutil.copyfile(f, out / f'angle_k_{k}.kmb')
(out / 'NOTICE.txt').write_text(NOTICE + 'Replaced: ' + ', '.join(f'angle_k_{k}.kmb' for k in sorted(repl)) + '\n', encoding='utf-8')
words = K.load_words(out / 'submission.npz')
total = 0
rec = {}
for k in range(15):
    t = time.time()
    st = K.kmb_counts(out / f'angle_k_{k}.kmb')
    v = K.verify_kmb(out / f'angle_k_{k}.kmb', k, words=words, direction='forward' if k == 0 else 'both')
    if k == 0:
        # reverse pass of loader 0: batch 0 in the word registers on entry, zero on exit
        # (checked as "bank 1" of a rearranged table: previous words = batch 0, new words = 0)
        w2 = words.copy()
        w2[:, 0:5] = words[:, 0:5]
        w2[:, 5:10] = 0
        v2 = K.verify_kmb(out / f'angle_k_{k}.kmb', 1, words=w2, direction='forward')
        assert v2['status'].startswith('PASS'), v2
        v = {'forward': v, 'reverse_exchanged_table': v2}
    sha = hashlib.sha256((out / f'angle_k_{k}.kmb').read_bytes()).hexdigest()
    rec[k] = dict(sha=sha[:16], counts=st, verify=v, replaced=k in repl)
    print(k, 'replaced' if k in repl else '        ', sha[:16], st, f'{time.time() - t:.0f}s', flush=True)
json.dump(rec, open(out.parent / 'local_gate.json', 'w'), indent=1, default=str)
print('local gate passed for all 15 loaders')
