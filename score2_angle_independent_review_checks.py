#!/usr/bin/env python3
"""Independent finite-basis checks of the root-owned affine block reducer."""
import hashlib
import json
from pathlib import Path
import random

from score2_clifford_affine_reduce import optimize, reduce_lines, parse


def execute(operations, wires, value):
    bits = {wire:(value >> index) & 1 for index,wire in enumerate(wires)}
    for gate, operands in operations:
        if gate == 'X':
            bits[operands[0]] ^= 1
        elif gate == 'CX':
            bits[operands[1]] ^= bits[operands[0]]
        elif gate == 'SWAP':
            a,b = operands
            bits[a],bits[b] = bits[b],bits[a]
        else:
            raise AssertionError(gate)
    return tuple(bits[wire] for wire in wires)


def main():
    randomizer = random.Random(20261115)
    cases, inputs, reductions = 0,0,0
    for n in range(2,7):
        wires = [2+3*i for i in range(n)]
        for trial in range(30):
            operations = []
            for _ in range(10+3*trial):
                gate = randomizer.choice(['X','CX','SWAP'])
                operands = tuple(randomizer.sample(wires,1 if gate == 'X' else 2))
                operations.append((gate,operands))
            candidate,_ = optimize(operations)
            assert len(candidate) <= len(operations)
            for value in range(1 << n):
                assert execute(operations,wires,value) == execute(candidate,wires,value)
                inputs += 1
            cases += 1
            reductions += len(candidate) < len(operations)
    barriers = ['CCX q0 q1 q2','HMR q3 b0','CZ q0 q1 if b0',
                'X q2 if b0','CX q1 q2 if b0','SWAP q1 q2 if b0',
                'PUSH_CONDITION b0','POP_CONDITION']
    block = ['X q0','CX q0 q1','CX q0 q1','X q0','X q1','X q1']
    lines = block.copy()
    for barrier in barriers:
        lines += [barrier] + block
    transformed,changes,counts = reduce_lines(lines)
    assert [line for line in transformed if parse(line) is None] == barriers
    root = Path(__file__).resolve().parent
    reviewed = ['score2_clifford_affine_reduce.py','score2_clifford_validate.py',
                'score2_dfthcsos_fixed_words_verify.py','score2_dfthcsos_candidate_verify.py']
    report = dict(status='PASS',method='Independent Boolean state enumeration; does not reuse reducer.affine',
                  random_seed=20261115,circuits=cases,basis_inputs=inputs,
                  circuits_with_gate_reduction=reductions,
                  nonaffine_and_conditional_barriers_preserved=barriers,
                  file_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in reviewed},
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (root/'score2_angle_independent_review_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
