"""Cost-oriented exact direct/toggle selection for an actual V79 phase plan.

MILP jointly selects all occurrences of a frequency and the required flag
constant rotations. Emission uses exact integer angle identities, borrowing a
provably-zero work wire when one is available and dirty echo otherwise.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

ROOT = Path(__file__).resolve().parents[2]
DONOR = ROOT / 'recovered' / 'V79'
sys.path.insert(0, str(DONOR))
from treewidth import TreeMulti, make_nodes
from emit_coset import Emitter, bits, MOD, W
from emit_coset_hmr import write_hmr
from native_kmb import NativeKMB
from affine_transport import cancel


def update_known(known, op):
    w, g = op.wires, op.raw
    def flip(q, control):
        if control == 0:
            return
        if control == 1 and known[q] is not None:
            known[q] ^= 1
        else:
            known[q] = None
    if g == 17:
        flip(w[0], 1)
    elif g == 33:
        flip(w[1], known[w[0]])
    elif g == 49:
        a, b = known[w[0]], known[w[1]]
        control = 0 if a == 0 or b == 0 else (1 if a == b == 1 else None)
        flip(w[2], control)
    elif g == 80:
        known[w[0]] = 0
    elif g in (19, 144, 160):
        pass
    else:
        raise ValueError(f'Unsupported gate for zero-state analysis: {g}')


def phase_availability(path):
    circuit = NativeKMB.read(path)
    known = [None]*W + [0]*(circuit.header[1]-W)
    costs = []
    for op in circuit.ops:
        if op.raw == 19:
            costs.append(1 if any(known[q] == 0 for q in range(W, len(known))) else 2)
        update_known(known, op)
    return costs


def select(source, mode, weight, output, budget=None):
    meta = json.loads(source.with_suffix('.json').read_text())
    availability = phase_availability(source.with_suffix('.kmb'))
    occurrences, base, plain = defaultdict(list), defaultdict(int), defaultdict(int)
    for tag, a, cost in zip(meta['tags'], map(int, meta['angles']), availability):
        kind, s, d, p, vs, hs = tag[:6]
        key = (d, p, tuple(vs), tuple(hs))
        if kind == 'toggle':
            occurrences[s].append((key, a, 2 if mode == 'dirty' else cost))
        elif kind == 'direct':
            base[key] += a
        elif kind == 'parity':
            plain[s] += a
    frequencies = [s for s, items in sorted(occurrences.items())
                   if plain[s] % MOD and sum(c for _, _, c in items) < weight]
    groups = sorted({k for s in frequencies for k, a, c in occurrences[s]
                     if not base[k] % MOD})
    group_index = {k: i+len(frequencies) for i, k in enumerate(groups)}
    rows, cols, values, nrows = [], [], [], 0
    for i, s in enumerate(frequencies):
        for key, angle, cost in occurrences[s]:
            if key in group_index:
                rows += [nrows, nrows]
                cols += [i, group_index[key]]
                values += [1., -1.]
                nrows += 1
    constraint_upper = [0.]*nrows
    if budget is not None:
        for i, s in enumerate(frequencies):
            rows.append(nrows); cols.append(i)
            values.append(float(sum(c for _, _, c in occurrences[s])))
        constraint_upper.append(float(budget)); nrows += 1
    objective = [sum(c for _, _, c in occurrences[s])-weight for s in frequencies]
    objective += [weight]*len(groups)
    if objective:
        constraint = LinearConstraint(coo_matrix((values, (rows, cols)),
                         shape=(nrows, len(objective))).tocsc(), -np.inf,
                         np.asarray(constraint_upper))
        result = milp(np.asarray(objective), integrality=np.ones(len(objective)),
                      bounds=Bounds(0, 1), constraints=constraint,
                      options={'time_limit': 40, 'mip_rel_gap': 0.0})
        assert result.x is not None
        selected = {s for i, s in enumerate(frequencies) if result.x[i] > .5}
        status, gap, value = int(result.status), float(result.mip_gap), float(result.fun)
    else:
        selected, status, gap, value = set(), 0, 0., 0.
    record = dict(mode=mode, rotation_weight=weight, source=str(source),ccx_budget=budget,
                  eligible=len(frequencies), groups=len(groups), constraints=nrows,
                  selected=len(selected), frequencies=sorted(selected),
                  direct_terms=sum(len(occurrences[s]) for s in selected),
                  estimated_extra_ccx=sum(c for s in selected for _, _, c in occurrences[s]),
                  mip_status=status, mip_gap=gap, proxy_delta=value)
    output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='frequencies'}), flush=True)
    return selected


class RotationMixin:
    def init_rotation_selection(self, adaptive):
        self.adaptive_clean = adaptive
        self.known = [None]*W + [0]*(self.Q-W)
        self.known_cursor = 0

    def clean_temp(self, forbidden):
        for op in self.ops[self.known_cursor:]:
            update_known(self.known, op)
        self.known_cursor = len(self.ops)
        return next((q for q in range(W, self.Q)
                     if self.known[q] == 0 and q not in forbidden), None)

    def sweep(self, flag, terms, d, p, V, H, *args):
        if flag is None:
            return Emitter.sweep(self, flag, terms, d, p, V, H)
        z = defaultdict(int)
        for s, a in terms:
            z[s] = (z[s]+a) % MOD
        take = {s:a for s,a in z.items() if s in self.S and s and a}
        rest = {s:a for s,a in z.items() if s not in take and a}
        rest[0] = (rest.get(0,0)+sum(take.values())) % MOD
        Emitter.sweep(self, flag, list(rest.items()), d, p, V, H)
        for s, a in sorted(take.items()):
            ps = list(bits(s)); t = ps[-1]
            for q in ps[:-1]:
                self.op(33, q, t)
            temp = self.clean_temp({flag, t}) if self.adaptive_clean else None
            if temp is not None:
                self.op(49, flag, t, temp)
                self.r(temp, -2*a, ('product',s,d,p,V,H,str(a)))
                self.erase(temp, [flag,t])
                self.stats['direct_clean_terms'] += 1
            else:
                assert d > 0 and t < W-d
                temp = W-1; b = (p>>(d-1)) & 1
                beta = -2*a*(1-2*b)
                self.op(49, flag, t, temp)
                self.r(temp, beta, ('borrow',s,d,p,V,H,str(a),temp))
                self.op(49, flag, t, temp)
                self.plain[1<<temp] -= beta
                self.stats['direct_dirty_terms'] += 1
            for q in ps[-2::-1]:
                self.op(33, q, t)
            self.stats['direct_frequency_terms'] += 1


class CostTree(RotationMixin, TreeMulti):
    pass


def emit(args, selected, prepared=None):
    start = time.time()
    P = json.loads((DONOR/'recip.plan.json').read_text())
    tree = make_nodes(P, args.width) if prepared is None else prepared[0]
    if prepared is not None:
        emitter = prepared[1]
        emitter.S = selected
        emitter.ops=[];emitter.angles=[];emitter.tags=[]
        emitter.plain=defaultdict(int);emitter.stats=Counter()
    elif args.scheduler == 'joint':
        sys.path.insert(0, str(ROOT/'synthesis'))
        from search_tree import SearchTree
        class CostJoint(RotationMixin, SearchTree):
            pass
        emitter = CostJoint(args.width, MOD//P['scale'], selected, 'auto',0,8,
                            policies=7,tries=2,persistent=True,hubs=True)
    else:
        emitter = CostTree(args.width, MOD//P['scale'], selected, 'auto',0,8)
    emitter.init_rotation_selection(args.mode != 'dirty')
    proxy = sum(emitter.split_cost(child)[0] for child in tree.ch.values())
    for child in tree.ch.values():
        emitter.split_tree(child)
    emitter.local_sweep(None,list(emitter.plain.items()),0,0,[],[])
    ops, _ = cancel(emitter.ops)
    target = args.stem.with_suffix('.kmb')
    write_hmr(NativeKMB.read(DONOR/'reference_header.kmb'), target,
              ops, emitter.angles, args.width, True)
    circuit = NativeKMB.read(target)
    counts = Counter(o.raw for o in circuit.ops)
    R = sum(a%(1<<125) != 0 for a in emitter.angles)
    T = sum(a%(1<<125)==0 and a%(1<<126)!=0 for a in emitter.angles)
    margin = 138112178
    tc = .56*math.log2((1<<64)*R/(math.pi*margin))+5.3
    stats = dict(width=args.width,ops=len(circuit.ops),ccx=counts[49],cx=counts[33],
                 rotations=len(emitter.angles),generic=R,t_base=T,hmr=counts[80],
                 scheduler=args.scheduler,mode=args.mode,proxy=proxy,
                 formula_cost_assuming_exact_phase=args.width*(counts[49]+(T+R*tc)/4),
                 sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                 seconds=time.time()-start, **emitter.stats)
    args.stem.with_suffix('.json').write_text(json.dumps(dict(stats=stats,
        tags=emitter.tags,angles=[str(a) for a in emitter.angles]),separators=(',',':')))
    print(json.dumps(stats,indent=2),flush=True)
    return tree, emitter


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--stem',type=Path,required=True)
    p.add_argument('--width',type=int,default=36)
    p.add_argument('--mode',choices=['dirty','adaptive'],default='adaptive')
    p.add_argument('--weight',type=float,default=8.28)
    p.add_argument('--scheduler',choices=['tree','joint'],default='tree')
    p.add_argument('--selection',type=Path)
    p.add_argument('--ccx-budget',type=int)
    p.add_argument('--budgets',type=int,nargs='*')
    a=p.parse_args();a.source=a.source.resolve();a.stem=a.stem.resolve()
    a.stem.parent.mkdir(parents=True,exist_ok=True)
    if a.budgets:
        import copy
        tasks=[]
        for budget in a.budgets:
            variant=copy.copy(a)
            variant.stem=a.stem.with_name(a.stem.name+f'_b{budget}')
            selected=select(a.source,a.mode,a.weight,
                            variant.stem.with_suffix('.selection.json'),budget)
            tasks.append((variant,selected))
        os.chdir(DONOR);prepared=None
        for variant,selected in tasks:
            prepared=emit(variant,selected,prepared)
        sys.exit(0)
    if a.selection:
        S=set(json.loads(a.selection.read_text())['frequencies'])
    else:
        S=select(a.source,a.mode,a.weight,a.stem.with_suffix('.selection.json'),a.ccx_budget)
    os.chdir(DONOR)
    emit(a,S)
