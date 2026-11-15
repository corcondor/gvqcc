"""Build a source-equivalent diagnostic KMB with explicit subroutine names."""
from argparse import ArgumentParser
from functools import wraps
import json
from pathlib import Path
import sys


def mark(module, attribute, label):
    if module is None or not hasattr(module, attribute):
        return
    original = getattr(module, attribute)
    if not callable(original):
        return

    @wraps(original)
    def annotated(builder, *args, **kwargs):
        with builder.mark(label):
            return original(builder, *args, **kwargs)

    setattr(module, attribute, annotated)


def main():
    p = ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--scan-positions", type=int, default=4095)
    args = p.parse_args()
    integration = str(args.source/"after_c5/integration_v3")
    release = str(args.source/"after_c5/release_v3/normalized")
    sys.path[:0] = [release, integration]
    import integration_paths  # noqa: F401
    sys.path[:0] = [release, integration]
    import integrated_pipeline as pipeline
    import kickmix as km
    pipeline.configure(pipeline.Options(True, True, True, True))

    for label, module, methods in (
        ("pipeline", pipeline, ("emit_key_prefix", "emit_key_closing")),
        ("extractor", pipeline.Extractor, ("emit_prefix", "emit_closing")),
        ("crt", pipeline.Synthesis, ("emit_prefix", "emit_closing")),
        ("outer", pipeline.Outer, ("emit_prefix", "emit_closing")),
        ("finish", pipeline.Finish, ("emit_prefix", "emit_closing")),
        ("scan", pipeline.Scan, ("emit",)),
        ("rolling_tail", pipeline.Tail, ("gauge_prefix", "gauge_return")),
        ("scalar_seed", pipeline.Seed, ("emit_prefix", "close_padded")),
        ("seam", pipeline.Seam, ("outer_closing_with_inverse", "finish_closing_keep_inverse")),
    ):
        for method in methods:
            mark(module, method, f"{label}.{method}")
    for obj, names in (
        (getattr(pipeline, "Window", None), ("emit_prefix", "emit_closing")),
        (getattr(pipeline, "SharedTensor", None), ("emit",)),
        (getattr(pipeline, "SharedTranspose", None), ("emit",)),
    ):
        if obj is not None:
            for method in names:
                mark(obj, method, f"{obj.__name__}.{method}")

    b = km.CircuitBuilder()
    b.set_max_qubits(889)
    syndromes = [b.create_quantum_register(12, f"S{i}") for i in range(70)]
    masks = [b.create_classical_register(12, f"E{i}") for i in range(4095)]
    print(json.dumps(pipeline.runtime_bindings()), flush=True)

    def stage(record):
        b.info_tag("stage:" + json.dumps(record, separators=(",", ":")))
        if isinstance(record, str):
            print(record, flush=True)

    pipeline.emit(b, syndromes, masks, j_min=15, scan_positions=args.scan_positions, stage=stage)
    c = b.finish_circuit()
    c.to_file(args.out,format="kmb")
    print(json.dumps(dict(operations=len(c), width=c.num_qubits)), flush=True)


if __name__ == "__main__":
    main()
