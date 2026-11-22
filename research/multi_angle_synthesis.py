#!/usr/bin/env python3
"""Four distinct *constructive*, reversible J=5 / 7-bit ANGLE compilers.

Algorithms:
  flat-minterm  : streamed 7-high equality, 4-low one-hot, per-row mask.
  split-minterm : 3+4 high-address one-hot caches, 4-low-address one-hot,
                  conditioned row mask fanout.
  split-anf     : same high caches, but Möbius/ANF low monomial cache and
                  conditioned coefficient masks per high block.
  split-basis   : factor each high-block (low monomial x 35 output) matrix
                  over GF(2); compute its independent output masks with a
                  corresponding low Boolean form, then conditioned fanout.

All use the X/CX/CCX gate set, no HMR, no measure; every scratch returns 0.
These are high-cost research constructions and NOT official KMB/score PASS.
For real-world evaluation: use the competition verifier on emitted native KMB
and account for its gate set / cost semantics; do not infer scores here.

Input: a 7-bit 75-column 'angle_words' array, N<=2048 valid addresses.
Every slot is a XOR transition (prev batch to new batch), never a new clean load.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Sequence
import numpy as np

TARGETS = tuple(11 + 8*j + b for j in range(5) for b in range(7))
TAGS = (18, 26, 34, 42, 50)
ALGORITHMS = ('flat-minterm', 'split-minterm', 'split-anf', 'split-basis')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()


def delta_table(words: np.ndarray, slot: int) -> np.ndarray:
    a = np.asarray(words, dtype=np.int64)
    if a.ndim != 2 or a.shape[1] != 75 or not 0 < len(a) <= 2048:
        raise ValueError('expected 1..2048 address rows and 75 angle words')
    if not 0 <= slot < 15 or np.any(a < 0) or np.any(a > 127):
        raise ValueError('invalid J5/7bit slot or word value')
    d = a[:, slot*5:(slot+1)*5].copy()
    if slot:
        d ^= a[:, (slot-1)*5:slot*5]
    return d


class Circuit:
    def __init__(self):
        self.gates: list[tuple[str,tuple[int,...]]] = []
        self.alloc = 51
        self.peak = 50
        self.counts = Counter()

    def new(self, number: int = 1) -> list[int]:
        result = list(range(self.alloc, self.alloc + number))
        self.alloc += number
        self.peak = self.alloc-1
        if self.alloc > 128:
            raise ValueError(f'ANGLE width >128 ({self.alloc})')
        return result

    def emit(self, op: str, *q: int):
        assert op in ('X','CX','CCX') and len(q) == {'X':1,'CX':2,'CCX':3}[op]
        assert len(set(q)) == len(q)
        self.gates.append((op, tuple(int(i) for i in q)))
        self.counts[op] += 1

    def undo(self, ops: Sequence[tuple[str,tuple[int,...]]]):
        # X, CX and CCX are each self-inverse.
        for op, qubits in reversed(ops):
            self.emit(op, *qubits)

    def kmx_lines(self):
        for q in range(11): yield f'APPEND_TO_REGISTER q{q} r0'
        yield 'REGISTER r0 "selection"'
        for q in range(11,51): yield f'APPEND_TO_REGISTER q{q} r1'
        yield 'REGISTER r1 "target"'
        for q in range(51,self.alloc): yield f'R q{q}'
        for op,q in self.gates:
            yield f'{op} ' + ' '.join(f'q{x}' for x in q)


def pair_flags(c: Circuit, a: int, b: int, out: list[int]):
    if len(out) != 4: raise ValueError('need 4 pair flags')
    for n in range(4):
        if not (n&1): c.emit('X',a)
        if not (n&2): c.emit('X',b)
        c.emit('CCX',a,b,out[n])
        if not (n&2): c.emit('X',b)
        if not (n&1): c.emit('X',a)


def onehot(c: Circuit, bits: Sequence[int]) -> list[int]:
    if len(bits) not in (3,4): raise ValueError('only 3 or 4')
    flags = c.new(1 << len(bits))
    pa = c.new(4)
    pair_flags(c,bits[0],bits[1],pa)
    if len(bits)==3:
        for n in range(8):
            if not (n&4): c.emit('X', bits[2])
            c.emit('CCX',pa[n&3],bits[2],flags[n])
            if not (n&4): c.emit('X', bits[2])
    else:
        pb=c.new(4)
        pair_flags(c,bits[2],bits[3],pb)
        for n in range(16):
            c.emit('CCX',pa[n&3],pb[n>>2],flags[n])
    return flags


def monomial_cache(c: Circuit) -> list[int|None]:
    """Low four bit monomials. Index is subset mask; mask 0 constant."""
    wire: list[int|None] = [None]*16
    for i in range(4): wire[1<<i]=i
    for size in (2,3,4):
        for mask in range(1,16):
            if mask.bit_count()!=size:continue
            msb = 1 << (mask.bit_length()-1)
            parent=mask^msb
            q=c.new()[0]
            c.emit('CCX',int(wire[parent]),msb.bit_length()-1,q)
            wire[mask]=q
    return wire


def word_masks(delta: np.ndarray) -> list[int]:
    """Each address row -> single 35-bit mask for dirty target XOR."""
    bits=[]
    for row in delta:
        mask=0
        for j,word in enumerate(row):
            mask |= int(word) << (7*j)
        bits.append(mask)
    return bits


def mobius_low_anf(rows: list[int]) -> list[int]:
    coeff=rows.copy()
    if len(coeff)!=16: raise ValueError('expect full/padded 16-low group')
    for bit in range(4):
        for s in range(16):
            if s&(1<<bit): coeff[s] ^= coeff[s^(1<<bit)]
    return coeff


def rank_output_basis(coeff: list[int]):
    """Return independent output masks and corresponding 4-bit low ANF forms.

    Vector-space elimination on output masks (35 bits). If an output mask
    is represented by basis bit t in coefficient at low monomial m, the
    corresponding low Boolean form t contains monomial m.
    """
    pivots: dict[int,tuple[int,int]] = {}
    selected=[]
    for v in coeff:
        original=v
        comb=0
        while v:
            p=v.bit_length()-1
            if p in pivots:
                row,bits=pivots[p]
                v ^= row
                comb ^= bits
            else:
                idx=len(selected)
                selected.append(original)
                pivots[p]=(v,comb ^ (1<<idx))
                break
    forms=[0]*len(selected)
    for monomial,outmask in enumerate(coeff):
        temp=outmask
        combination=0
        while temp:
            p=temp.bit_length()-1
            if p not in pivots: raise AssertionError('not in output span')
            row,bits=pivots[p]
            temp ^= row
            combination ^= bits
        for i in range(len(selected)):
            if (combination>>i)&1:
                forms[i] ^= 1<<monomial
    # Assert factorization exactly recovers all original ANF output vectors.
    for m,expected in enumerate(coeff):
        recomposed=0
        for outmask,lowform in zip(selected,forms):
            if (lowform>>m)&1: recomposed ^= outmask
        if recomposed!=expected: raise AssertionError('rank decomposition wrong')
    return selected,forms


def emit_fanout(c: Circuit, control: int, out_mask: int):
    for j,q in enumerate(TARGETS):
        if (out_mask>>j)&1:
            c.emit('CX',control,q)



def synthesize_flat(delta: np.ndarray, slot: int):
    """Standalone 82Q DNF oracle, with streamed 7-bit high equality."""
    rows=word_masks(delta)
    blocks=math.ceil(len(rows)/16)
    c=Circuit()
    low=onehot(c,(0,1,2,3))
    base=tuple(c.gates)
    chain=c.new(6)
    active=c.new()[0]
    used=0
    for h in range(blocks):
        inv=[4+i for i in range(7) if (h>>i)&1==0]
        for q in inv:c.emit('X',q)
        high_ops=[]
        high_ops.append(('CCX',(4,5,chain[0])))
        for i in range(2,7):
            high_ops.append(('CCX',(chain[i-2],4+i,chain[i-1])))
        for op,qs in high_ops:c.emit(op,*qs)
        for lo in range(16):
            a=16*h+lo
            if a>=len(rows):break
            if not rows[a]:continue
            used+=1
            c.emit('CCX',chain[5],low[lo],active)
            emit_fanout(c,active,rows[a])
            c.emit('CCX',chain[5],low[lo],active)
        c.undo(high_ops)
        for q in reversed(inv):c.emit('X',q)
    c.undo(base)
    stat=dict(c.counts)
    stat.update(method='flat-minterm',slot=slot,addresses=len(rows),
                output_terms=used,qubits=c.alloc,n_high_blocks=blocks)
    return c,stat


def synthesize(words: np.ndarray, slot: int, method: str):
    if method not in ALGORITHMS: raise ValueError(method)
    delta=delta_table(words,slot)
    if method=='flat-minterm':
        return synthesize_flat(delta,slot)
    rows=word_masks(delta)
    blocks=math.ceil(len(rows)/16)
    c=Circuit()
    pre_start=len(c.gates)
    high3=onehot(c,(4,5,6))
    high4=onehot(c,(7,8,9,10))
    if method=='split-minterm':
        low_flags=onehot(c,(0,1,2,3))
        low_mono=None
    else:
        low_flags=None
        low_mono=monomial_cache(c)
    precomputation=tuple(c.gates[pre_start:])
    high_flag, active = c.new(2)
    low_tmp=c.new()[0] if method=='split-basis' else None
    terms=0
    stats=Counter()
    for h in range(blocks):
        group=rows[h*16:(h+1)*16]
        if method!='split-minterm':
            coeff=mobius_low_anf(group+[0]*(16-len(group)))
            if method=='split-anf':
                factored=[(mask, 1<<monomial) for monomial,mask in enumerate(coeff) if mask]
            else:
                outputs, lowforms=rank_output_basis(coeff)
                factored=list(zip(outputs,lowforms))
        else:
            factored=[(mask,1<<lo) for lo,mask in enumerate(group) if mask]
        if not factored:continue
        c.emit('CCX', high3[h&7], high4[h>>3], high_flag)
        for mask,low_poly in factored:
            if method=='split-minterm':
                lo=low_poly.bit_length()-1
                c.emit('CCX',high_flag,int(low_flags[lo]),active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high_flag,int(low_flags[lo]),active)
            elif method=='split-anf':
                mono=low_poly.bit_length()-1
                if mono==0:
                    emit_fanout(c,high_flag,mask)
                    stats['high_only_terms']+=1
                else:
                    c.emit('CCX',high_flag,int(low_mono[mono]),active)
                    emit_fanout(c,active,mask)
                    c.emit('CCX',high_flag,int(low_mono[mono]),active)
            else:
                # A general low Boolean form: XOR monomials into one clean
                # scratch, multiply by current high equality, fan out, undo.
                if low_poly==1:
                    emit_fanout(c,high_flag,mask)
                    stats['high_only_terms']+=1
                elif low_poly & (low_poly-1)==0:
                    mono=low_poly.bit_length()-1
                    if mono==0: raise AssertionError
                    c.emit('CCX',high_flag,int(low_mono[mono]),active)
                    emit_fanout(c,active,mask)
                    c.emit('CCX',high_flag,int(low_mono[mono]),active)
                else:
                    ops=[]
                    for mono in range(16):
                        if (low_poly>>mono)&1:
                            if mono==0:ops.append(('X',(low_tmp,)))
                            else:ops.append(('CX',(int(low_mono[mono]),low_tmp)))
                    for op,qq in ops:c.emit(op,*qq)
                    c.emit('CCX',high_flag,low_tmp,active)
                    emit_fanout(c,active,mask)
                    c.emit('CCX',high_flag,low_tmp,active)
                    c.undo(ops)
                    stats['composite_low_forms']+=1
            terms+=1
        c.emit('CCX', high3[h&7], high4[h>>3], high_flag)
        stats['active_high_blocks']+=1
    c.undo(precomputation)
    stat=dict(c.counts)
    stat.update(method=method, slot=slot, addresses=len(rows), output_terms=terms,
                qubits=c.alloc, n_high_blocks=blocks,
                **dict(stats))
    return c,stat


def prove(c: Circuit, delta: np.ndarray, dirty_seed: int = 7) -> dict:
    """Bitparallel exact XOR oracle over ALL valid addresses and dirty targets.

    This is a logical equality proof with no phase-bearing gates, but NOT
    official KickMix/quantum verifier status.
    """
    n=len(delta)
    mask=(1<<n)-1
    init=[0]*c.alloc
    for q in range(11):
        init[q]=sum(((a>>q)&1)<<a for a in range(n))
    rng=np.random.default_rng(dirty_seed)
    for q in range(11,51):
        init[q]=int.from_bytes(rng.bytes((n+7)//8),'little')&mask
    st=init.copy()
    for op,q in c.gates:
        if op=='X':st[q[0]]^=mask
        elif op=='CX':
            if q[0] in range(11,51): raise AssertionError('dirty control')
            st[q[1]]^=st[q[0]]
        elif op=='CCX':
            if q[0] in range(11,51) or q[1] in range(11,51):
                raise AssertionError('dirty control')
            st[q[2]]^=st[q[0]] & st[q[1]]
        else: raise AssertionError('wrong gate')
    expected=word_masks(delta)
    for i,q in enumerate(TARGETS):
        toggled=sum(((expected[a]>>i)&1)<<a for a in range(n))
        if st[q]!= (init[q]^toggled):
            raise AssertionError(('mismatched target',i,q))
    for q in list(range(11))+list(TAGS):
        if st[q]!=init[q]: raise AssertionError(('changed address/tag',q))
    for q in range(51,c.alloc):
        if st[q]: raise AssertionError(('dirty scratch',q))
    return dict(all_valid_addresses=True, arbitrary_dirty_targets=True,
                scratch_clean=True, tags_unchanged=True,
                zero_relative_phase_by_X_CX_CCX=True)


def run(seeds: list[Path], out: Path, methods: list[str], emit_samples: bool=True):
    out.mkdir(parents=True,exist_ok=True)
    ledger=out/'experiments.jsonl'
    seen=set()
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            if line.strip(): seen.add(json.loads(line)['experiment_id'])
    rows=[]
    for fp in seeds:
        with np.load(fp,allow_pickle=False) as z:
            words=z['angle_words'].astype(np.int64)
        source_hash=sha256(fp)
        for method in methods:
            for slot in range(15):
                key=hashlib.sha256(f'{source_hash}|{method}|{slot}|multi-v1'.encode()).hexdigest()
                if key in seen: continue
                c,stat=synthesize(words,slot,method)
                proof=prove(c,delta_table(words,slot))
                rec=dict(schema='gvqcc.multiangle.v1',experiment_id=key,
                         source=fp.name,source_sha256=source_hash,
                         **stat,**proof,official_kickmix_pass=False,
                         new_score=None)
                if emit_samples and slot in (0,1):
                    sample=out/f'{fp.stem}__{method}__k{slot}.kmx'
                    sample.write_text('\n'.join(c.kmx_lines())+'\n')
                    rec['sample_kmx_sha256']=sha256(sample)
                    rec['sample_kmx_name']=sample.name
                with ledger.open('a') as f:
                    f.write(json.dumps(rec,ensure_ascii=False,sort_keys=True)+'\n')
                    f.flush()
                seen.add(key)
                rows.append(rec)
                if slot in (0,7,14):
                    print(fp.name,method,'slot',slot,'Q',c.alloc,'CCX',stat.get('CCX',0),'CX',stat.get('CX',0),flush=True)
    all_records=[json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    totals={}
    for rec in all_records:
        key=rec['source']+'|'+rec['method']
        totals.setdefault(key,dict(source=rec['source'],method=rec['method'],Q_peak=0,CCX=0,CX=0,X=0,slots=0))
        bucket=totals[key]
        bucket['Q_peak']=max(bucket['Q_peak'],rec['qubits'])
        for field in ('CCX','CX','X'): bucket[field]+=rec.get(field,0)
        bucket['slots']+=1
    summary=dict(schema='gvqcc.multiangle.summary.v1',algorithms=list(ALGORITHMS),
                 groups=sorted(totals.values(),key=lambda r:(r['source'],r['CCX'])),
                 evidence='Exact bitparallel XOR; KMX emitted only for slot0+1; not native KickMix',
                 records=len(all_records))
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    with (out/'comparisons.csv').open('w',newline='') as f:
        cols=['source','method','Q_peak','CCX','CX','X','slots']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(summary['groups'])
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',nargs='+',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--methods',nargs='+',choices=ALGORITHMS,default=ALGORITHMS)
    p.add_argument('--no-samples',action='store_true')
    a=p.parse_args()
    print(json.dumps(run(a.seeds,a.out,a.methods,not a.no_samples)['groups'],indent=2))


if __name__=='__main__':main()