"""Count basis work lanes that can be replaced by products at their uses."""
from collections import defaultdict
from pathlib import Path
import json
import sys

import kickmix as km


def find_leaf_lanes(path):
    circuit = km.Circuit.from_file(path)
    state = defaultdict(list)
    writes = defaultdict(list)
    for position, line in enumerate(str(circuit).splitlines()):
        gate, *args = line.split()
        wires = [int(arg[1:]) for arg in args if arg.startswith("q")]
        for offset, wire in enumerate(wires):
            state[wire].append((position, gate, offset, wires))
            if gate in {"X", "CX", "CCX"} and offset == len(wires)-1:
                writes[wire].append(position)
    recipes = []
    for wire in range(51, circuit.num_qubits):
        trace = state[wire]
        if len(trace) < 3 or [x[1] for x in [*trace[:2], trace[-1]]] != ["R", "CCX", "HMR"]:
            continue
        sources = trace[1][3][:-1]
        uses = trace[2:-1]
        if any(gate != "CX" or offset != 0 for _, gate, offset, _ in uses):
            continue
        if any(wires[-1] in sources for _, _, _, wires in uses):
            continue
        if any(trace[1][0] < pos < trace[-1][0] for factor in sources for pos in writes[factor]):
            continue
        recipes.append({"wire": wire, "sources": sources, "uses": len(uses), "extra": len(uses)-1})
    return {"k": path.stem, "qubits": circuit.num_qubits,
            "eligible": sorted(recipes, key=lambda item: (item["extra"], item["wire"]))}


if __name__ == "__main__":
    source = Path(sys.argv[1])
    rows = [find_leaf_lanes(source / f"angle_k_{k}.kmb") for k in range(1, 15)]
    print(json.dumps(rows, indent=2))
