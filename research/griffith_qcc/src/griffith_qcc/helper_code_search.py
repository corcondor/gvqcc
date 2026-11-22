"""Joint five-LUT4 temporal code search across ALL 15 V8 ANGLE banks.

All physically equivalent sign gauges are parameterized by five shared helper
Boolean truth tables h_j(low4). A linear-time exact Givens sign projection
installs any code into every angle of a row. Search varies five 16-entry LUTs
(80 bits) simultaneously and measures a 15-bank low×high GF(2) tensor-rank
PROXY. It does not claim those ranks equal emitted KickMix Toffoli counts.

The binarized LUT variables and Pareto selection are Griffith-inspired, but
this implementation is original. No upstream Griffith source is included.
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from .chemistry import rank_gf2
from .temporal_gauge import project_table

BASE16=[(1<<16)-1]+[sum(((a>>j)&1)<<a for a in range(16)) for j in range(4)]


def helper_rank(tables)->int:
    return rank_gf2(BASE16+list(map(int,tables)))


def original_helpers(words):
    return tuple(sum(((((int(words[a,j])>>5)^(int(words[a,j])>>6))&1)<<a) for a in range(16)) for j in range(5))


def instantiate(words,tree_edges,helpers):
    if len(helpers)!=5 or any(h<0 or h>65535 for h in helpers):
        raise ValueError('five 16-bit truth tables required')
    n=len(words)
    desired=np.zeros_like(words)
    for j,h in enumerate(helpers):
        vals=np.asarray([(h>>(a%16))&1 for a in range(n)],dtype=desired.dtype)
        desired[:,j::5]=vals[:,None]<<5
    return project_table(words,desired,tree_edges)[0]


def rank16(rows):
    d={}
    for x in rows:
        x=int(x)
        while x:
            t=x.bit_length()-1
            if t not in d:d[t]=x;break
            x^=d[t]
    return len(d)


def tensor_rank_proxy(words):
    """15-bank independent bit-plane ranks of mixed high×low interaction.

    Uses a fixed zero completion of invalid addresses 1219..1231; a real
    compiler may choose a more favorable completion. The ranks are proxies,
    not lower bounds on CCX in the unrestricted multi-output XAG model.
    """
    w=np.zeros((1232,75),dtype=np.uint8)
    w[:len(words)]=words
    w=w.reshape(77,16,15,5)
    weights=(1<<np.arange(16,dtype=np.uint32))
    perbank=[]
    for k in range(15):
        delta=w[:,:,k].copy()
        if k:delta^=w[:,:,k-1]
        bits=((delta[:,:,:,None]>>np.arange(7,dtype=np.uint8))&1).reshape(77,16,35)
        # Each 16-bit row is the truth table of one 4-bit low-address function.
        rows=np.einsum('hlo,l->ho',bits.astype(np.uint32),weights,optimize=True)
        # Remove separable high-only/low-only contributions.
        rem=rows ^ rows[0:1,:]
        rem ^= np.where(rem&1,np.uint32(65535),np.uint32(0))
        ranks=[rank16(rem[:,i]) for i in range(35)]
        perbank.append(sum(ranks))
    return {'per_bank_cross_ranks':perbank,'sum_cross_ranks':sum(perbank)}


@dataclass
class SearchStep:
    step:int
    score:int
    best:int
    flips:int
    rank:int


def search(words,edges,*,steps=120,seed=20261122,mutation_scale=1):
    """Elitist stochastic search with a learned mutation probability per code bit.

    For each candidate, evaluates all fifteen Boolean output tensors at once.
    After a successful move its changed helper LUT bit gets a higher mutation
    probability; unsuccessful changes are downweighted. This is a lightweight
    bandit-style online learning rule, not a fully differentiable KMB trainer.
    """
    rnd=random.Random(seed)
    start=original_helpers(words)
    if helper_rank(start)!=10:
        raise ValueError('source five helper LUTs are not independent modulo affine')
    current=start
    current_words=instantiate(words,edges,current)
    current_score=tensor_rank_proxy(current_words)['sum_cross_ranks']
    best=current;best_words=current_words.copy();best_score=current_score
    bias=[1.0]*80
    ledger=[SearchStep(0,current_score,best_score,0,10)]
    for s in range(1,steps+1):
        flipcount=rnd.randint(1,mutation_scale)
        flips=rnd.choices(range(80),weights=bias,k=flipcount)
        proposal=list(current)
        for bit in flips:proposal[bit//16]^=1<<(bit%16)
        proposal=tuple(proposal)
        if helper_rank(proposal)!=10:
            for bit in flips:bias[bit]=max(.1,bias[bit]*.98)
            continue
        proposed_words=instantiate(words,edges,proposal)
        proposed_score=tensor_rank_proxy(proposed_words)['sum_cross_ranks']
        if proposed_score<current_score:
            current=proposal;current_score=proposed_score
            for bit in flips:bias[bit]=min(12.,bias[bit]*1.15)
        else:
            for bit in flips:bias[bit]=max(.1,bias[bit]*.995)
        if proposed_score<best_score:
            best_score=proposed_score;best=proposal;best_words=proposed_words
        ledger.append(SearchStep(s,proposed_score,best_score,len(flips),helper_rank(proposal)))
    return {'source_helpers':[int(x) for x in start],
            'initial_rank_proxy':ledger[0].score,
            'best_helpers':[int(x) for x in best],
            'best_rank_proxy':best_score,
            'best_words':best_words,'steps':[v.__dict__ for v in ledger],
            'num_proposals':steps,'note':'This is a rank PROXY, not native KMB Toffoli.'}
