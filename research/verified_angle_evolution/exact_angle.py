"""Independent, exact bit-packed ANGLE contract checker for KMB v2.

Checks all valid 1,220 selection addresses in both passes. HMR measurement
outcomes are formal independent variables; each must cancel exactly.
A check is a mathematical isometry proof on the reachable batch inputs, NOT
an official competition verifier, and not arbitrary-target correctness.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from kmb_v2 import Circuit, Gate

N=1220
MASK=(1<<N)-1
ADDR=[sum(((a>>j)&1)<<a for a in range(N)) for j in range(11)]
OUTPUT_Q=range(11,51)

@dataclass
class Check:
    status: str
    circuits: int
    transitions: int
    measurement_phases: int
    ccx: int
    max_qubits: int
    outputs_digest: str


def run(circuit: Circuit, incoming: Sequence[int], label='') -> tuple[list[int],int]:
    if len(incoming)!=40: raise ValueError('40 packed word bits expected')
    if circuit.nqubits>128: raise ValueError(f'{label}: exceeds 128 qubits')
    if circuit.nqubits<51:raise ValueError('wrong wire width')
    state = ADDR + list(incoming) + [0]*(circuit.nqubits-51)
    pending={}
    hmrs=0
    for pos, g in enumerate(circuit.ops):
        name=g.name
        q=g.q
        if len(set(q))!=len(q):raise AssertionError((label,pos,'duplicate qubits',q))
        if name=='CX':
            state[q[1]]^=state[q[0]]
        elif name=='X':
            state[q[0]]^=MASK
        elif name=='CCX':
            state[q[2]]^=state[q[0]]&state[q[1]]
        elif name=='R':
            if state[q[0]]:raise AssertionError((label,pos,'nonzero reset',q[0]))
        elif name=='HMR':
            bit=g.bit[0]
            if pending.get(bit,0):raise AssertionError((label,pos,'pending HMR phase',bit))
            pending[bit]=state[q[0]]
            state[q[0]]=0
            hmrs+=1
        elif name=='CZ_IF':
            bit=g.cond[0]
            if bit not in pending:raise AssertionError((label,pos,'unbound HMR bit',bit))
            pending[bit]^=state[q[0]]&state[q[1]]
        else:
            raise ValueError((label,pos,'unsupported operation',name))
    if state[:11]!=ADDR:raise AssertionError((label,'address not restored'))
    if any(state[51:]):raise AssertionError((label,'unclean scratch'))
    if any(pending.values()):raise AssertionError((label,'residual relative phase'))
    return state[11:51],hmrs


def verify(circuits: Sequence[Circuit], reference:Sequence[Sequence[int]]|None=None)-> tuple[Check,list[list[int]]]:
    """A baseline defines the true outputs; later versions must match it exactly."""
    import hashlib
    if len(circuits)!=15:raise ValueError('Exactly 15 J=5 circuits required')
    expected=[]
    current=[0]*40
    n_hmr=0
    for k,circuit in enumerate(circuits):
        current,h=run(circuit,current,f'forward{k}')
        n_hmr+=h
        if reference is not None and current!=list(reference[k]):
            bad=next(j for j,(x,y) in enumerate(zip(current,reference[k])) if x!=y)
            diff=current[bad]^reference[k][bad]
            raise AssertionError(('incorrect forward output',k,bad,(diff&-diff).bit_length()-1))
        expected.append(current.copy())
    for k in range(14,-1,-1):
        current,h=run(circuits[k],current,f'reverse{k}')
        n_hmr+=h
        desired=expected[k-1] if k else [0]*40
        if current!=desired:
            bad=next(j for j,(x,y) in enumerate(zip(current,desired)) if x!=y)
            diff=current[bad]^desired[bad]
            raise AssertionError(('incorrect reverse output',k,bad,(diff&-diff).bit_length()-1))
    a=hashlib.sha256()
    for word in expected:
        for w in word:a.update(int(w).to_bytes((N+7)//8,'little'))
    return Check('EXACT_REACHABLE_FWD_REVERSE_AND_ALL_HMR_BRANCHES',15,30*N,n_hmr,
                 sum(g.name=='CCX' for c in circuits for g in c.ops),
                 max(c.nqubits for c in circuits),a.hexdigest()),expected
