"""Place source annotations on e4 using exact neighboring operand sequences."""

from argparse import ArgumentParser
import json
import mmap
from pathlib import Path
from struct import unpack_from
import sys


def strip_tags(tagged, output, binary, fmt):
    with tagged.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        magic, *values = fmt.HEADER.unpack_from(data)
        fields = dict(zip(fmt.HEADER_FIELDS, values))
        prefix_end = fmt.HEADER.size
        for _ in range(fields["num_registers"]):
            kind, size = fmt.PACKET.unpack_from(data, prefix_end)
            assert not kind
            prefix_end += 16 + size
        packets = {}
        pos = prefix_end
        for expected in range(1, 12):
            kind, size = fmt.PACKET.unpack_from(data, pos)
            assert kind == expected
            packets[kind] = (pos+16, pos+16+size)
            pos += 16 + size
        assert pos == len(data)
        ops = data[slice(*packets[1])]
        tags = [i for i, op in enumerate(ops) if op == 6]
        assert len(tags) == fields["num_info_tags"]
        tags_begin, tags_end = packets[11]
        starts = unpack_from("<" + "Q" * (len(tags)+1), data, tags_begin)
        chars = tags_begin + 8 * len(starts)
        assert chars + starts[-1] == tags_end
        names = [data[chars+l:chars+r].decode() for l,r in zip(starts,starts[1:])]
        marks = [(i-count, name) for count, (i, name) in enumerate(zip(tags, names))]
        no_tags = ops.replace(b"\x06", b"")
        del ops
        fields["num_ops"] = len(no_tags)
        fields["num_info_tags"] = fields["num_info_tag_chars"] = 0
        with output.open("wb") as dst:
            dst.write(fmt.HEADER.pack(magic, *(fields[name] for name in fmt.HEADER_FIELDS)))
            binary.copy_range(data, dst, fmt.HEADER.size, prefix_end)
            dst.write(fmt.PACKET.pack(1, len(no_tags)))
            dst.write(no_tags)
            for kind in range(2,11):
                lo, hi = packets[kind]
                dst.write(fmt.PACKET.pack(kind, hi-lo))
                binary.copy_range(data, dst, lo, hi)
            dst.write(fmt.PACKET.pack(11, 8))
            dst.write(b"\0" * 8)
    return marks


def align_cut(position, reference, base, match):
    for length in (4096, 2048, 8192, 1024, 512):
        hits = []
        for side in ("before", "after"):
            if side == "before":
                start, stop = position - length, position
            else:
                start, stop = position, position + length
            if start < 0 or stop > len(reference.opcodes):
                continue
            pattern = reference.opcodes[start:stop]
            if len(set(pattern)) < 2:
                continue
            cursor = 0
            raw = []
            while (index := base.opcodes.find(pattern, cursor)) >= 0:
                cursor = index + 1
                raw.append(index)
                if len(raw) > 16:
                    break
            if not raw or len(raw) > 16:
                continue
            original = tuple(reference.operations(start, stop))
            candidates = []
            for index in raw:
                if match(original, base.operations(index, index+length)) is not None:
                    candidates.append(index + position - start)
                    if len(candidates) > 1:
                        break
            if len(candidates) == 1:
                hits.append((candidates[0], side))
        if hits:
            indices = sorted({i for i,_ in hits})
            return dict(candidates=indices, anchor_length=length, sides=hits)
    return dict(candidates=[])


def align_marks(marks, reference, base, match):
    candidates = {}
    active = []
    scopes = []
    for position, label in marks:
        if position not in candidates:
            candidates[position] = align_cut(position, reference, base, match)
        if label.startswith("@enter:"):
            active.append((label[7:], position, len(active)))
        elif label.startswith("@exit:"):
            original, start, depth = active.pop()
            assert label[6:] == original
            scopes.append(dict(label=original, source=[start,position], depth=depth))
    assert not active
    for scope in scopes:
        a, b = (candidates[pos]["candidates"] for pos in scope["source"])
        if len(a) == len(b) == 1 and a[0] < b[0]:
            scope["e4"] = [a[0],b[0]]
    events = [dict(source=position, label=label, **candidates[position])
              for position,label in marks if label.startswith("stage:")]
    return scopes, events


def main():
    p = ArgumentParser(description=__doc__)
    for name in ("tagged","strip","e4","out","repo","census"):
        p.add_argument("--"+name, type=Path, required=True)
    p.add_argument("--coarse", action="store_true")
    args = p.parse_args()
    sys.path[:0] = [str(args.census), str(args.repo)]
    from census import PIN, digest, open_columns
    import dqi_ccx_peephole as binary
    import kmb_profile as fmt
    from outcome_dqi_chart_match import match
    assert digest(args.e4) == PIN
    marks = strip_tags(args.tagged, args.strip, binary, fmt)
    if args.coarse:
        names = ("pipeline.", "extractor.", "outer.", "seam.", "finish.",
                 "rolling_tail.", "scalar_seed.", "scan.")
        marks = [(i,label) for i,label in marks if
                 (label.startswith(("@enter:","@exit:"))
                  and label.split(":",1)[1].startswith(names))
                 or label in ("stage:\"odd_border_and_elimination\"",
                              "stage:\"odd_full_preimage\"",
                              "stage:\"raw_boundary\"",
                              "stage:\"shared_seam_undo_odd_full_preimage\"",
                              "stage:\"shared_seam_restored_raw_inputs\"")]
    source = open_columns(args.strip, binary.BinaryCircuit, fmt)
    e4 = open_columns(args.e4, binary.BinaryCircuit, fmt)
    try:
        scopes, events = align_marks(marks, source, e4, match)
    finally:
        source.close()
        e4.close()
    result = dict(source=digest(args.tagged), e4=PIN,
                  scope_count=len(scopes), mapped_scopes=sum("e4" in r for r in scopes),
                  stage_events=events, scopes=scopes)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print({k:v for k,v in result.items() if k not in ("scopes","stage_events")})


if __name__ == "__main__":
    main()
