#!/usr/bin/env python3
"""Read-only residual input-factor scan: older matches and central meetings.

Uses the original exact identity and conservative commutation rules, but lets
both CCXs move to a common point inside the interval. All earlier matching
signatures within the window are considered, not only the latest one.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import resource
import signal
import time

import dqi_ccx_input_factor as original
import dqi_ccx_peephole as shared


def meeting_split(first, second, middle):
    """Find k with first commuting across middle[:k], second across middle[k:]."""
    first_stop, split, count = None, 0, 0
    for index, operation in enumerate(middle):
        count += 1
        if first_stop is None and not shared.commutes_with_ccx(first, operation):
            first_stop = index
        if not shared.commutes_with_ccx(second, operation):
            split = index + 1
        if first_stop is not None and split > first_stop:
            return None
    return split, count


def scan(circuit, window, deadline):
    history = defaultdict(deque)
    expiry = deque()
    last_position = -1
    counts = dict(ccx_scanned=0, signature_pairs=0, four_distinct_pairs=0,
                  eligible_commuting_pairs=0, central_meeting_pairs=0,
                  older_than_latest_pairs=0, pairs_beyond_256=0,
                  barrier_resets=0)
    hits = []
    complete = True
    for rank, match in enumerate(shared.THREE_QUBIT.finditer(circuit.opcodes)):
        position = match.start()
        if (circuit.opcodes[position] & 0x7F) != 0x31:
            continue
        if time.monotonic() > deadline:
            complete = False
            break
        counts['ccx_scanned'] += 1
        current = circuit.ccx_at(position, rank)
        if shared.BARRIER.search(circuit.opcodes, last_position + 1, position):
            history.clear()
            expiry.clear()
            counts['barrier_resets'] += 1
        last_position = position
        while expiry and expiry[0][0] < position - window:
            past, signature = expiry.popleft()
            queue = history.get(signature)
            if queue and queue[0].source_index == past:
                queue.popleft()
                if not queue:
                    del history[signature]
        signatures = [(current.qubits[2], q, current.condition) for q in current.qubits[:2]]
        for signature in signatures:
            for age, earlier in enumerate(reversed(history.get(signature, ()))):
                counts['signature_pairs'] += 1
                operands = original.pair_operands(earlier, current)
                if operands is None:
                    continue
                counts['four_distinct_pairs'] += 1
                result = meeting_split(earlier, current,
                                       circuit.operations(earlier.source_index + 1, position))
                if result is None:
                    continue
                split, middle_count = result
                central = 0 < split < middle_count
                counts['eligible_commuting_pairs'] += 1
                counts['central_meeting_pairs'] += int(central)
                counts['older_than_latest_pairs'] += int(age > 0)
                counts['pairs_beyond_256'] += int(position - earlier.source_index > 256)
                hits.append(dict(first_source_op=earlier.source_index,
                                 second_source_op=position,
                                 qubits_a_b_c_t=list(operands),
                                 explicit_condition_bit=current.condition,
                                 middle_count=middle_count, meeting_split=split,
                                 central_meeting=central, prior_match_age=age,
                                 source_distance=position - earlier.source_index))
        for signature in signatures:
            history[signature].append(current)
            expiry.append((position, signature))
    return counts, hits, complete


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--window', type=int, default=4096)
    parser.add_argument('--seconds', type=float, default=240)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))
    started = time.monotonic()
    deadline = started + min(args.seconds, 240)
    report = dict(input=str(args.input), window=args.window,
                  max_seconds=min(args.seconds, 240), memory_limit_bytes=1 << 30,
                  scope='Read-only residual scan; no file mutation or full simulation',
                  identity_proof=original.identity_check(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    circuit = None
    try:
        profile = shared.kp.profile(args.input, max_register_summaries=0)
        report['input_sha256'] = profile['raw_kmb_sha256']
        report['header'] = profile['header']
        circuit = shared.BinaryCircuit(args.input, profile)
        counts, hits, complete = scan(circuit, args.window, deadline)
        report.update(status='COMPLETE' if complete else 'TIME_BOUNDED_PARTIAL',
                      counts=counts, hits=hits, additional_ccx_reduction_proven=0,
                      candidate_written=False,
                      caveat='Overlapping discovered pairs are not yet a jointly applicable rewrite list.')
    except MemoryError:
        report.update(status='MEMORY_LIMIT', candidate_written=False)
    finally:
        if circuit is not None:
            circuit.close()
        report.update(elapsed_seconds=time.monotonic()-started,
                      max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        args.report.write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({k: v for k, v in report.items() if k not in ('hits', 'header')}, indent=2))


if __name__ == '__main__':
    main()
