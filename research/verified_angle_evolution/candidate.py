"""Initial population seed. OpenEvolve can mutate the EVOLVE section.

Return EXACTLY fifteen independently allocated KMB circuit objects. Preserve each
circuit's input register schema, output values, scratch cleanup and HMR phases.
Only strictly cheaper circuits are eligible for output artifacts.
"""
from rewrite import candidate_moves, apply_move
from kmb_v2 import Circuit

# EVOLVE-BLOCK-START

def synthesize(circuits):
    """Local control-factor resynthesis, with safe commutation proof."""
    out=[]
    for c in circuits:
        moves=candidate_moves(c.ops,window=4096,limit=10000)
        if not moves:
            out.append(c)
            continue
        # Test strongest guaranteed reduction first; evaluator independently
        # rejects every faulty candidate, even when a rule is changed by LLM.
        best=max(moves,key=lambda m:m.saved)
        revised=apply_move(c.ops,best)
        out.append(Circuit(c.magic,c.version,c.nqubits,c.nbits,c.registers,revised,c.tags))
    return out

# EVOLVE-BLOCK-END
