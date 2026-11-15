"""Export the ordered quantum/classical dependency DAG of a certified ANGLE circuit."""
from argparse import ArgumentParser
from collections import Counter
import gzip
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import kickmix as km

WIRE = re.compile(r"(?<!\S)([qb]\d+)(?!\S)")
ARITIES = {
    "X": (1, 0), "R": (1, 0), "CX": (2, 0), "CCX": (3, 0),
    "SWAP": (2, 0), "HMR": (1, 1), "CZ": (2, 1),
}
REGISTER = {"REGISTER", "APPEND_TO_REGISTER"}


def extract(lines):
    """One node/operation and one edge per consecutive touch of each wire."""
    latest = {}
    inputs = set()
    nodes = []
    declarations = []
    for i, line in enumerate(lines):
        op = line.split()[0]
        if op in REGISTER:
            declarations.append([i, line])
            continue
        wires = WIRE.findall(line)
        assert (sum(w[0] == "q" for w in wires),
                sum(w[0] == "b" for w in wires)) == ARITIES[op], line
        assert len(set(wires)) == len(wires)
        assert (op == "CZ") == (" if " in line)
        incoming = [[wire, latest.get(wire, -1)] for wire in wires]
        inputs.update(wire for wire, index in incoming if index == -1)
        nodes.append([i, line, incoming])
        latest.update((wire, i) for wire in wires)
    return {
        "schema": "kickmix-ordered-wire-dag-v1",
        "edge_direction": "producer to consumer, -1 means input",
        "declarations": declarations,
        "inputs": sorted(inputs),
        "nodes": nodes,
        "outputs": [[wire, index] for wire, index in sorted(latest.items())],
    }


def restore(document):
    """Check transmitted graph edges, then use the original topological order."""
    assert document["schema"] == "kickmix-ordered-wire-dag-v1"
    ordered = document["declarations"] + [[i, line] for i, line, _ in document["nodes"]]
    ordered.sort()
    assert [i for i, _ in ordered] == list(range(len(ordered)))
    lines = [line for _, line in ordered]
    rebuilt = extract(lines)
    assert all(document[key] == value for key, value in rebuilt.items())
    return km.Circuit("\n".join(lines) + "\n")


def canonical(circuit):
    with TemporaryDirectory() as work:
        path = Path(work) / "restored.kmb"
        circuit.to_file(path, format="kmb")
        return path.read_bytes()


def export(source, path=None):
    payload = source.read_bytes()
    lines = str(km.Circuit.from_file(BytesIO(payload), format="kmb")).splitlines()
    document = extract(lines)
    document["source_kmb_sha256"] = sha256(payload).hexdigest()
    if path is not None:
        body = json.dumps(document, separators=(",", ":")).encode()
        path.write_bytes(gzip.compress(body, mtime=0))
        document = json.loads(gzip.decompress(path.read_bytes()))
    assert canonical(restore(document)) == payload
    stats = Counter(line.split()[0] for _, line, _ in document["nodes"])
    edges = Counter(w[0] for _, _, links in document["nodes"] for w, previous in links
                    if previous >= 0)
    report = {
        "file": source.name, "kmb_sha256": document["source_kmb_sha256"],
        "operations": sum(stats.values()), "instructions": dict(stats), "edges": dict(edges),
        "register_declarations": len(document["declarations"]), "roundtrip_byte_identical": True,
    }
    if path is not None:
        report["compressed_graph_sha256"] = sha256(path.read_bytes()).hexdigest()
        report["compressed_graph_bytes"] = path.stat().st_size
    return report


def main():
    parser = ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("export")
    verify.add_argument("family", type=Path)
    verify.add_argument("output", type=Path)
    verify.add_argument("--publish-batch", type=int, default=1)
    replay = commands.add_parser("restore")
    replay.add_argument("graph", type=Path)
    replay.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "restore":
        document = json.loads(gzip.decompress(args.graph.read_bytes()))
        payload = canonical(restore(document))
        assert sha256(payload).hexdigest() == document["source_kmb_sha256"]
        args.output.write_bytes(payload)
        return
    args.output.mkdir(parents=True, exist_ok=True)
    reports = []
    for batch in range(15):
        name = f"angle_k_{batch}"
        path = args.output / f"{name}.graph.json.gz" if batch == args.publish_batch else None
        reports.append(export(args.family / f"{name}.kmb", path))
    (args.output / "circuit_graph_receipt.json").write_text(
        json.dumps(reports, indent=2) + "\n")


if __name__ == "__main__":
    main()
