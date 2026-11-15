"""A zero-Toffoli-saving but exact, lower-Clifford-count evolved seed."""
from heuristics import optimize

# EVOLVE-BLOCK-START

def synthesize(circuits):
    result,_=optimize(circuits,window=48,ccx_window=4096)
    return result

# EVOLVE-BLOCK-END
