#!/usr/bin/env python3
"""Bounded one-AND relocation of *joint* nested phase complements.

The target is h=f XOR g where g<=f.  This differs from score2, which
searched the individual g.  A positive model must pass all legal inputs.
The immutable score2 C++ quotient solver is used without modification.
"""
import argparse
import hashlib
import json
import random
import subprocess
import time
from pathlib import Path

import score_invsqrt_retire as R
from score2_invsqrt_phase_relocation import PANEL
from score6_invsqrt_joint_phase import PIN


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def simulate(ops):
    panel = [{**p, 'start': p['start']+4, 'phase': p['phase']+4,
              'end': p['end']+4} for p in PANEL]
    wanted = [p for p in panel if p['old_ANDs'] == 2]
    cuts = {p['start']-1 for p in wanted} | {p['phase'] for p in wanted}
    domain, values = R.initial_values()
    stack, phases = [], {}
    for i, (op, qs) in enumerate(ops):
        if i in cuts:
            assert op == 'Z_POW' and not stack
            phases[i] = values[qs[0]]
        if op == 'PUSH_CONDITION':
            stack.append(values[:])
        elif op == 'POP_CONDITION':
            saved = stack.pop()
            assert saved == values
            values = saved
        else:
            R.advance(op, qs, values, domain)
    targets = []
    for p in wanted:
        f, g = phases[p['start']-1], phases[p['phase']]
        assert not (g & ~f)
        targets.append((p, f ^ g))
    return panel, targets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--seconds', type=float, default=110)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).parent
    source = root/'score3_invsqrt_cache.kmx'
    assert sha(source) == PIN
    lines, ops = R.instructions(source)
    panel, targets = simulate(ops)
    solver_source = root/'score2_invsqrt_relocate_oneand.cpp'
    binary = args.out/'oneand_solver'
    subprocess.run(['g++', '-O3', '-std=c++17', str(solver_source), '-o',
                    str(binary)], check=True, timeout=30)
    rng = random.Random(620261115)
    samples = list(range(1, 129))
    for k in range(1, 23):
        lo, hi = 1 << (k-1), min((1 << k)-1, R.MAX_X)
        if lo <= hi:
            samples += [rng.randrange(lo, hi+1) for _ in range(16)]
    samples = list(dict.fromkeys(samples))
    while len(samples) < 512:
        x = rng.randrange(1, R.MAX_X+1)
        if x not in samples:
            samples.append(x)
    records = []
    began = time.monotonic()
    for iteration in range(4):
        width = len(samples)
        nw, sd = (width+63)//64, (1 << width)-1
        sig = [sum(((x >> q) & 1) << j for j, x in enumerate(samples))
               for q in range(22)] + [0]*24
        ts = [sum(((v >> x) & 1) << j for j, x in enumerate(samples))
              for _, v in targets]
        domain, values = R.initial_values()
        stack, sample_stack, snapshots = [], [], []
        for i, (op, qs) in enumerate(ops):
            if op == 'PUSH_CONDITION':
                stack.append(values[:]); sample_stack.append(sig[:])
            elif op == 'POP_CONDITION':
                before, sb = stack.pop(), sample_stack.pop()
                assert before == values and sb == sig
                values, sig = before, sb
            else:
                R.advance(op, qs, values, domain)
                R.advance(op, qs, sig, sd)
            cut = i+1
            if stack or op not in ('CCX', 'CSWAP', 'HMR'):
                continue
            if any(p['start'] <= cut <= p['end'] for p in panel):
                continue
            zeros = sum(1 << q for q, v in enumerate(values) if not v)
            if zeros:
                snapshots.append((cut, zeros, sig[:]))
        def words(v):
            return [(v >> (64*j)) & ((1 << 64)-1) for j in range(nw)]
        packed = [nw, len(snapshots), len(targets)] + words(sd)
        for (p, _), v in zip(targets, ts):
            packed += [p['start'], p['end']] + words(v)
        for cut, zeros, sig in snapshots:
            packed += [cut, zeros]
            for v in sig:
                packed += words(v)
        inp = args.out/f'round{iteration}.txt'
        inp.write_text(' '.join(map(str, packed))+'\n')
        remaining = args.seconds-(time.monotonic()-began)
        if remaining <= 0:
            records.append({'status': 'EXTERNAL_TIME_LIMIT_BEFORE_SOLVER'})
            break
        try:
            run = subprocess.run([str(binary), str(inp)], capture_output=True,
                                 text=True, timeout=remaining, check=True)
        except subprocess.TimeoutExpired as e:
            stderr = e.stderr or b''
            if isinstance(stderr, bytes):
                stderr = stderr.decode()
            (args.out/f'round{iteration}_progress.jsonl').write_text(stderr)
            records.append({'status': 'EXTERNAL_TIME_LIMIT', 'iteration': iteration,
                            'complete': False})
            break
        (args.out/f'round{iteration}_progress.jsonl').write_text(run.stderr)
        result = json.loads(run.stdout)
        result.update(iteration=iteration, samples=width)
        if result['status'] == 'SAMPLE_MODEL':
            domain, values = R.initial_values(); stack = []
            for op, qs in ops[:result['cut']]:
                if op == 'PUSH_CONDITION':
                    stack.append(values[:])
                elif op == 'POP_CONDITION':
                    before = stack.pop(); assert before == values; values = before
                else:
                    R.advance(op, qs, values, domain)
            assert not stack
            def expr(mask):
                value = 0
                for q in range(46):
                    if mask >> q & 1:
                        value ^= values[q]
                return value
            left, right = expr(result['left_mask']), expr(result['right_mask'])
            lm = result['affine_mask_constant_then_qubits']
            actual = (left & right) ^ expr(lm >> 1) ^ (domain if lm & 1 else 0)
            p, target = targets[result['target_index']]
            result['feature'] = p
            diff = actual ^ target
            if not diff:
                result.update(status='FULL_DOMAIN_IDENTITY_VERIFIED', legal_inputs=R.MAX_X)
                records.append(result)
                break
            x = (diff & -diff).bit_length()-1
            result.update(full_domain_check='FAIL', counterexample=x)
            samples.append(x)
        records.append(result)
        if result['status'] != 'SAMPLE_MODEL':
            break
    report = dict(
        source_path=str(source), source_sha256=PIN, script_sha256=sha(__file__),
        solver_source_path=str(solver_source), solver_source_sha256=sha(solver_source),
        solver_binary_sha256=sha(binary), legal_inputs=R.MAX_X,
        elapsed_seconds=time.monotonic()-began, budget_seconds=args.seconds,
        identity='g<=f; alpha*f+beta*g=(alpha+beta)*f-beta*(f XOR g)',
        scope='Four two-AND joint complements, depth-zero nonlinear/reset cuts '
              'with a full-domain-zero scratch outside all eight removable gadgets. '
              'Left parity: any single or pair of wires, or any parity of flags '
              'q22..q25,q7 plus one wire. Right and affine remainder unrestricted. '
              'Negative sample result excludes this family on the full domain; '
              'general two-factor synthesis is not exhausted.',
        records=records, candidate_created=False)
    (args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
