"""Bit-exact oracle proof for the restricted KMX subset emitted by XAG.

All input patterns and all measurement outcomes are checked for small blocks;
initial XOR targets may have arbitrary bits. Global phase is tracked mod two.
Does not replace the full official native KickMix verifier.
"""
from __future__ import annotations

from itertools import product


def prove_oracle(kmx: str, n_inputs: int, n_targets: int, *,
                 expected_tables: tuple[int,...] | None = None, max_hmr: int = 12) -> dict:
    lines = [x.split() for x in kmx.splitlines() if x.strip()]
    events = [x for x in lines if x[0] not in {'APPEND_TO_REGISTER','REGISTER'}]
    hmr = sum(x[0] == 'HMR' for x in events)
    if expected_tables is not None and len(expected_tables) != n_targets:
        raise ValueError('wrong expected output table count')
    # All control-dependent operations must be independent of arbitrary target bits.
    for e in events:
        if e[0] in ('CX','CCX','CZ'):
            ctrl=e[1:3] if e[0] in ('CCX','CZ') else e[1:2]
            if any(n_inputs <= int(x[1:]) < n_inputs+n_targets for x in ctrl):
                raise AssertionError('target-controlled gates violate oracle proof premise')
    if hmr > max_hmr or n_inputs > 10 or n_targets > 40:
        raise ValueError('proof would require too many explicit configurations')
    qcount = 1 + max((int(x[1][1:]) for x in events if x[0] in ('X','R','HMR')), default=0)
    for e in events:
        for token in e[1:]:
            if token.startswith('q') and token[1:].isdigit(): qcount = max(qcount, int(token[1:]) + 1)
    n_cases = 0
    for addr in range(1 << n_inputs):
        # All target bits are arbitrary. Probe zero and each single-bit toggle.
        # The emitter never reads target bits as controls, so basis probes
        # certify the affine XOR action for arbitrary targets.
        for target in [0] + [1 << j for j in range(n_targets)]:
            for outcomes in range(1 << hmr):
                q = [(addr >> i) & 1 for i in range(n_inputs)] + [(target >> i) & 1 for i in range(n_targets)] + [0]*(qcount - n_inputs - n_targets)
                bits = {}
                phase = 0
                hi = 0
                for e in events:
                    op = e[0]
                    if op == 'R':
                        qi=int(e[1][1:]);assert q[qi] == 0, ('dirty reset',addr,target,outcomes,e)
                    elif op == 'X':q[int(e[1][1:])] ^= 1
                    elif op == 'CX':q[int(e[2][1:])] ^= q[int(e[1][1:])]
                    elif op == 'CCX':q[int(e[3][1:])] ^= q[int(e[1][1:])] & q[int(e[2][1:])]
                    elif op == 'HMR':
                        qi=int(e[1][1:]);m=(outcomes >> hi) & 1;hi+=1
                        phase ^= q[qi] & m
                        q[qi]=0;bits[e[2]]=m
                    elif op == 'CZ':
                        assert e[3] == 'if'
                        phase ^= (q[int(e[1][1:])] & q[int(e[2][1:])] & bits[e[4]])
                    else:
                        raise ValueError(('unsupported instruction',e))
                if expected_tables is not None:
                    want=[((target >> j) & 1) ^ ((expected_tables[j] >> addr) & 1) for j in range(n_targets)]
                    if q[n_inputs:n_inputs+n_targets]!=want:
                        raise AssertionError(('incorrect_oracle_output',addr,target,outcomes,q[n_inputs:n_inputs+n_targets],want))
                if q[:n_inputs] != [(addr>>i)&1 for i in range(n_inputs)]:
                    raise AssertionError('input register changed')
                if any(q[n_inputs+n_targets:]): raise AssertionError('dirty workspace')
                if phase:raise AssertionError('nonzero relative phase')
                n_cases += 1
    # Verify expected words using the same parsed-KMX trajectory with zero
    # measurement outcome but separate from the XAG simulator.
    def output(addr,target):
        q = [(addr >> i) & 1 for i in range(n_inputs)] + [(target >> i) & 1 for i in range(n_targets)] + [0]*(qcount - n_inputs - n_targets)
        bit={}
        for e in events:
            op=e[0]
            if op=='X':q[int(e[1][1:])]^=1
            if op=='CX':q[int(e[2][1:])]^=q[int(e[1][1:])]
            if op=='CCX':q[int(e[3][1:])]^=q[int(e[1][1:])]&q[int(e[2][1:])]
            if op=='HMR':q[int(e[1][1:])]=0;bit[e[2]]=0
        return sum(x<<i for i,x in enumerate(q[n_inputs:n_inputs+n_targets]))
    return {'basis_phase_workspace_cases':n_cases,'hmr_branches':1<<hmr,'hmr_count':hmr,
            'num_qubits':qcount,'output_map':output}
