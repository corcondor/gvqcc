# Kaggle CPU job (private, offline): search 233-Toffoli head loaders.  args: budget_minutes k:nrel:e [k:nrel:e ...]
import os, subprocess, shutil, time, sys, glob

T0 = time.time()
budget = float(sys.argv[1]) * 60
plan = [tuple(int(v) for v in a.split(':')) for a in sys.argv[2:]]
OUT = '/kaggle/working'
W = os.path.join(OUT, 'w')
shutil.copytree(os.environ['KV_DATASET'], W)
CODE = os.path.join(W, 'code')


def sh(c):
    print(c, flush=True)
    subprocess.run(c, shell=True, check=True)


sh('lscpu | head -n 20')
sh(f'g++ -O3 -march=native -funroll-loops -std=c++17 -pthread -w -o {CODE}/phase1bs5.exe {CODE}/phase1bs5.cpp')
sh(f'g++ -O3 -march=native -funroll-loops -std=c++17 -pthread -w -o {CODE}/hsolve.exe {CODE}/hsolve.cpp')
os.chmod(f'{CODE}/phase1bs5.exe', 0o755)
os.chmod(f'{CODE}/hsolve.exe', 0o755)
env = dict(os.environ, P1THREADS='4', PYTHONUNBUFFERED='1')
done = set()
seed = 100
while time.time() - T0 < budget and len(done) < len(plan):
    for k, nrel, e in plan:
        if (k, nrel) in done or time.time() - T0 >= budget:
            continue
        seed += 1
        log = f'{OUT}/make2_k{k}_r{nrel}_s{seed}.log'
        left = budget - (time.time() - T0)
        limit = min(600, max(60, left - 240))
        with open(log, 'w') as fl:
            try:
                subprocess.run([sys.executable, '-u', 'make2.py', str(k), f'{W}/covers/cover95_k{k}_s1.pkl', str(nrel), str(e), str(seed), str(limit)],
                               cwd=CODE, env=env, stdout=fl, stderr=subprocess.STDOUT, timeout=left + 600)
            except subprocess.TimeoutExpired:
                fl.write('TIMEOUT\n')
        txt = open(log).read()
        lines = [l for l in txt.splitlines() if not l.startswith('  chip')]
        if 'emitted' in txt:                       # always keep an emitted circuit (re-verified locally anyway)
            for f in glob.glob(os.path.join(CODE, f'angle_k_{k}_n95_f{nrel}_s{seed}.kmb')) + glob.glob(os.path.join(CODE, f'p1_k{k}_s{seed}_*')):
                shutil.copy(f, OUT)
        if "'status': 'PASS" in txt and 'Traceback' not in txt:
            kmb = f'angle_k_{k}_n95_f{nrel}_s{seed}.kmb'
            shutil.copy(os.path.join(CODE, kmb), OUT)
            for f in glob.glob(os.path.join(CODE, f'p1_k{k}_s{seed}_*')):
                shutil.copy(f, OUT)
            done.add((k, nrel))
            print(f'[{time.time() - T0:.0f}s] PASS loader {k} nrel {nrel} seed {seed}', flush=True)
        else:
            print(f'[{time.time() - T0:.0f}s] fail loader {k} seed {seed}: {lines[-1][:200] if lines else ""}', flush=True)
        for f in glob.glob(os.path.join(CODE, 'p1_*.prog')):
            print('   ', os.path.basename(f), open(f).read().splitlines()[:3])
            os.remove(f)
shutil.rmtree(W)
print('done', sorted(done), flush=True)
