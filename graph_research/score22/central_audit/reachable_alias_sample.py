"""Measure affine rank around the degree-34 CRT residue on decoder inputs."""

from argparse import ArgumentParser
import json
from pathlib import Path
import struct
import sys
from tempfile import TemporaryDirectory

import numpy as np

from alias_99 import rank
from census import digest, open_columns
from splice_plu_crt import locate
from split_crt import words


def binary_rows(values):
    return ((values[:, None, :] >> np.arange(12, dtype=np.uint32)[None, :, None]) & 1).reshape(
        -1, values.shape[-1],
    )


def affine_rank(bits):
    columns = np.packbits(bits, axis=1, bitorder="little")
    vals = [int.from_bytes(row.tobytes(), "little") for row in columns]
    return rank([*vals, (1 << bits.shape[1]) - 1])


def evaluate(source, state, r, i):
    field = source.F
    _, kappa = source.node(i)
    n, d, p = [words(x) for x in state]
    product = np.vectorize(field.mul, otypes=[np.uint32])
    scalar = np.zeros(n.shape, dtype=np.uint32)
    for beta in range(r):
        nv = np.zeros(n.shape[1], dtype=np.uint32)
        dv = nv.copy()
        for j, w in enumerate(n):
            nv ^= product(w, field.pow(beta, j))
        for j, w in enumerate(d):
            dv ^= product(w, field.pow(beta, j))
        pv = p[0] ^ product(beta, p[1])
        qc = field.mul(beta, beta) ^ beta ^ kappa
        scalar[beta] = product(qc, nv) ^ product(pv, dv)
    lo = np.zeros(n.shape[1], dtype=np.uint32)
    hi = lo.copy()
    for (a, b), w in zip(source.residue_powers(i, r + 1), d):
        lo ^= product(a, w)
        hi ^= product(b, w)
    t, _ = source.node(i)
    return scalar, np.array([p[0] ^ product(t, p[1]), p[1]]), np.array([lo, hi])


def tighten_header(path, source, end, fmt):
    """Recompute maximum operand IDs after truncating the native input."""
    maxima = [0, 0]
    fields = dict(source.profile["header"])
    pos = fmt.HEADER.size
    for _ in range(fields["num_registers"]):
        _, length = fmt.PACKET.unpack_from(source.data, pos)
        pos += fmt.PACKET.size
        name, size = struct.unpack_from("<II", source.data, pos)
        ids = np.frombuffer(source.data, dtype="<u4", offset=pos + 8 + name, count=size)
        for mode in (0, 1):
            matches = ids[(ids >> 31) == mode] & 0x7FFFFFFF
            if matches.size:
                maxima[mode] = max(maxima[mode], int(matches.max()) + 1)
        del ids
        pos += length
    for kind in range(2, 10):
        _, stop = source.column_range(kind, 0, end)
        if stop:
            ids = np.frombuffer(source.data, dtype="<u4",
                                offset=source.packets[kind]["payload_offset"], count=stop // 4)
            mode = int(kind <= 7)
            maxima[mode] = max(maxima[mode], int(ids.max()) + 1)
            del ids
    with path.open("r+b") as stream:
        _, *raw = fmt.HEADER.unpack(stream.read(fmt.HEADER.size))
        fields = dict(zip(fmt.HEADER_FIELDS, raw))
        fields.update(num_bits=maxima[0], num_qubits=maxima[1])
        stream.seek(0)
        stream.write(fmt.HEADER.pack(fmt.MAGIC, *(fields[key] for key in fmt.HEADER_FIELDS)))


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("decoder", type=Path)
    cli.add_argument("reference_prefix", type=Path)
    cli.add_argument("report", type=Path)
    cli.add_argument("--source-sha", required=True)
    cli.add_argument("--prior-code", type=Path, required=True)
    cli.add_argument("--dqisrc", type=Path, required=True)
    cli.add_argument("--verifier", type=Path, required=True)
    cli.add_argument("--shots", type=int, default=1024)
    args = cli.parse_args()
    assert digest(args.decoder) == args.source_sha
    for path in (args.prior_code, args.verifier.parent, *(args.dqisrc / d for d in (
        "night_c27/synthesis", "night_c27/arithmetic", "after_c5/extractor_width",
    ))):
        sys.path.insert(0, str(path))
    import dqi_ccx_peephole as binary
    import ew_paths  # noqa: F401
    import fused_crt_synthesis as synthesis
    import kickmix as km
    import kmb_profile
    import kmb_splice
    from outcome_dqi_chart_match import match
    import verify_submission_dqi as official

    def open_path(path):
        return open_columns(path, binary.BinaryCircuit, kmb_profile)

    base = open_path(args.decoder)
    template = open_path(args.reference_prefix)
    start, stop, maps = locate(base, template, 0, len(template.opcodes), match)
    print("Sampling actual prefix to", start, flush=True)
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "prefix.kmb"
        kmb_splice.write_segments(path, base, [(base, 0, start)])
        tighten_header(path, base, start, kmb_profile)
        circuit = km.Circuit.from_file(path)
    spec = official.ProblemSpecDQI.benchmark_instance(num_shots=args.shots)
    rng = np.random.default_rng(182457)
    syndromes, mbuc, _ = official.sample_shots(
        spec, official.FieldTables(km.GF2Field(spec.degree)), rng, args.shots)
    s_reg, e_reg, _ = official.validate_registers(circuit, spec)
    sim = km.Simulator(batch_size=args.shots, seed=521398, counting_operations=False)
    sim.use_same_registers_as(circuit)
    sim.write_across_shots(km.array(s_reg), official.to_bits(syndromes, spec.degree))
    sim.write_across_shots(km.array(e_reg), official.to_bits(mbuc, spec.degree))
    sim.do(circuit)
    r, i = 34, 0
    data = [np.asarray(sim.read_across_shots(km.array([km.q(maps["qubits"][j])
                                                     for j in range(lo, hi)])))
            for lo, hi in ((0, 408), (408, 828), (828, 852))]
    n, p, d = evaluate(synthesis, data, r, i)
    bits = binary_rows(np.vstack([n, p]))
    ndp = binary_rows(np.vstack([n, p, d]))
    response = dict(
        source_sha256=args.source_sha, sample_distribution="stock DQI syndrome and mask sampler",
        sampled_shots=args.shots, entry_to_bound_r34_stage=start, end_of_original_stage=stop,
        output_scalar_and_old_P_bits=bits.shape[0],
        output_scalar_and_old_P_affine_rank_including_constant=affine_rank(bits),
        output_scalar_old_P_and_D_bits=ndp.shape[0],
        output_scalar_old_P_and_D_affine_rank_including_constant=affine_rank(ndp),
        chart_low_zero_high_nonzero=int(np.count_nonzero((d[0] == 0) & (d[1] != 0))),
        zero_source_count=int(np.count_nonzero((d[0] | d[1]) == 0)),
        scope="Actual production prefix values on sampled verifier-distribution inputs. "
              "A full rank is a witness against a fixed affine dependency on these inputs, "
              "not a claim about every nonlinear encoding.",
    )
    args.report.write_text(json.dumps(response, indent=2) + "\n")
    print(response, flush=True)
    base.close()
    template.close()


if __name__ == "__main__":
    main()
