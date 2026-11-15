#!/usr/bin/env python3
"""Build and verify the complete score2 portfolio from the previous notebook output.

CPU-only, no network, no credentials, no competition submission. The 15 changed
ANGLE circuits and a byte-exact NPZ patch are embedded by the local builder.
The exact public DQI821 circuit and inverse e46 are retained byte-for-byte.
"""
from pathlib import Path, PurePosixPath
import base64
import hashlib
import importlib.util
import io
import json
import lzma
import os
import shutil
import sys
import tempfile
import time
import zipfile

BUILD = __BUILD_JSON__
PAYLOAD_B64 = __PAYLOAD_B64__


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def log(event, **details):
    print(json.dumps({'event': event, **details}), flush=True)


def expected_members():
    return {'dqi.kmb', 'invsqrt.kmb', 'dfthcsos/submission.npz'} | {
        f'dfthcsos/angle_k_{i}.kmb' for i in range(15)}


def checked_members(z):
    infos = z.infolist()
    require(len(infos) == 18 and set(z.namelist()) == expected_members(),
            'Expected the exact 18-member portfolio')
    for info in infos:
        p = PurePosixPath(info.filename)
        require(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename,
                'Unsafe archive path')
        require(not info.is_dir() and not (info.flag_bits & 1), 'Invalid ZIP member')
    return infos


def raw_npz_chunks(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos = sorted(z.infolist(), key=lambda x: x.header_offset)
        require(len(infos) == len({i.filename for i in infos}), 'Duplicate NPZ arrays')
        return {a.filename: data[a.header_offset:(infos[i + 1].header_offset
                    if i + 1 < len(infos) else z.start_dir)] for i, a in enumerate(infos)}


def restore_family(base_npz, destination):
    require(sha_bytes(base_npz) == BUILD['baseline_npz_sha256'], 'Wrong baseline NPZ')
    packed = base64.b64decode(PAYLOAD_B64, validate=True)
    require(sha_bytes(packed) == BUILD['payload_sha256'], 'Embedded payload checksum failed')
    raw = lzma.decompress(packed)
    require(sha_bytes(raw) == BUILD['payload_uncompressed_sha256'], 'Uncompressed checksum failed')
    source_chunks = raw_npz_chunks(base_npz)
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        require(set(z.namelist()) == set(BUILD['payload_members']), 'Unexpected payload members')
        for name, digest in BUILD['loaders'].items():
            data = z.read(name)
            require(sha_bytes(data) == digest, 'Loader checksum: ' + name)
            (destination / name).write_bytes(data)
        recipe = json.loads(z.read('npz_recipe.json'))
        candidate = b''.join(source_chunks[r['name']] if r['same']
                             else z.read('npz_chunks/' + r['name']) for r in recipe)
        candidate += z.read('npz_tail.bin')
    require(sha_bytes(candidate) == BUILD['candidate_npz_sha256'], 'Reconstructed NPZ checksum failed')
    (destination / 'submission.npz').write_bytes(candidate)
    return candidate


def find_base(root):
    for p in sorted(root.rglob('submission.zip')):
        try:
            with zipfile.ZipFile(p) as z:
                checked_members(z)
                if sha_bytes(z.read('dfthcsos/submission.npz')) != BUILD['baseline_npz_sha256']:
                    continue
                good = True
                for name in ('invsqrt.kmb', 'dqi.kmb'):
                    h = hashlib.sha256()
                    with z.open(name) as f:
                        for b in iter(lambda: f.read(8 << 20), b''):
                            h.update(b)
                    good &= h.hexdigest() in (BUILD['base_dqi_sha256'] if name == 'dqi.kmb' else [BUILD['unchanged_members'][name]])
                if good:
                    return p
        except (OSError, zipfile.BadZipFile, RuntimeError):
            continue
    raise RuntimeError('Attach the output of geocpuresearch/gvqcc-verified-480ccx-gauge128, version 1')


def find_dqi(root, base, scratch):
    expected = BUILD['unchanged_members']['dqi.kmb']
    for p in sorted(root.rglob('*.kmb')):
        if p.stat().st_size == BUILD['dqi_bytes'] and sha_file(p) == expected:
            return p
    # A recovered original portfolio may already contain the exact circuit.
    with zipfile.ZipFile(base) as z:
        if z.getinfo('dqi.kmb').file_size == BUILD['dqi_bytes']:
            target = scratch / 'dqi821.kmb'
            with z.open('dqi.kmb') as src, target.open('xb') as dst:
                record = stream_copy(src, dst)
            if record['sha256'] == expected:
                return target
            target.unlink()
    raise RuntimeError('Attach manwithacat/vqcc-apache-public-circuits: exact 821bf8d157c0.kmb is required')


def find_official(root):
    for p in sorted(root.rglob('verify.py')):
        if p.parent.name != 'dfthcsos' or p.parent.parent.name != 'verifiers':
            continue
        candidate = p.parents[2]
        if all((candidate / name).is_file() and sha_file(candidate / name) in hashes
               for name, hashes in BUILD['official_pins'].items()):
            return candidate
    raise RuntimeError('The pinned competition verifier and engine are missing')


def stream_copy(src, dst):
    h = hashlib.sha256()
    size = 0
    for b in iter(lambda: src.read(8 << 20), b''):
        dst.write(b)
        h.update(b)
        size += len(b)
    return {'sha256': h.hexdigest(), 'bytes': size}


def package(base, family, output, dqi_source):
    require(not output.exists(), 'Output ZIP already exists')
    records = []
    with zipfile.ZipFile(base) as old, zipfile.ZipFile(output, 'x', allowZip64=True) as new:
        for info in checked_members(old):
            if info.filename == 'dqi.kmb':
                source = dqi_source.open('rb')
                expected = BUILD['unchanged_members']['dqi.kmb']
            elif info.filename.startswith('dfthcsos/'):
                source = (family / Path(info.filename).name).open('rb')
                expected = BUILD['candidate_npz_sha256'] if info.filename.endswith('.npz') else BUILD['loaders'][Path(info.filename).name]
            else:
                source = old.open(info)
                expected = BUILD['unchanged_members'][info.filename]
            with source as src, new.open(info, 'w', force_zip64=True) as dst:
                record = stream_copy(src, dst)
            require(record['sha256'] == expected, 'Packaged member mismatch: ' + info.filename)
            records.append({'member': info.filename, **record})
    with zipfile.ZipFile(output) as z:
        checked_members(z)
        require(z.testzip() is None, 'Written ZIP CRC validation failed')
    return records


def main():
    start = time.monotonic()
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    input_root, output = Path('/kaggle/input'), Path('/kaggle/working')
    require(input_root.is_dir() and output.is_dir(), 'Run this worker in Kaggle')
    require(not (output / 'submission.zip').exists(), 'Use a fresh notebook run')
    base = find_base(input_root)
    official = find_official(input_root)
    scratch = Path(tempfile.mkdtemp(prefix='gvqcc-score2-submit-', dir='/tmp'))
    dqi_source = find_dqi(input_root, base, scratch)
    family = scratch / 'dfthcsos'
    with zipfile.ZipFile(base) as z:
        original = z.read('dfthcsos/submission.npz')
    candidate = restore_family(original, family)
    log('inputs_verified', source=str(base), candidate_npz_sha256=sha_bytes(candidate))
    sys.path.insert(0, str(official / 'kickmix'))
    sys.path.insert(0, str(official / 'verifiers'))
    import numpy as np
    with np.load(io.BytesIO(original), allow_pickle=False) as z:
        before = {k: z[k] for k in z.files}
    with np.load(io.BytesIO(candidate), allow_pickle=False) as z:
        after = {k: z[k] for k in z.files}
    require(set(before) == set(after), 'NPZ array set changed')
    require(all(np.array_equal(before[k], after[k]) for k in before if k not in ('H2_I', 'angle_words')),
            'Unexpected array change')
    require(np.count_nonzero(before['angle_words'] != after['angle_words']) == 20, 'Expected 20 changed words')
    spec = importlib.util.spec_from_file_location('official_submission_v5', official / 'verifiers/dfthcsos/verify.py')
    verifier = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = verifier
    spec.loader.exec_module(verifier)
    circuits = [family / f'angle_k_{i}.kmb' for i in range(15)]
    words, layout, toffoli = verifier.recover_words_from_circuits(
        verifier.load_circuits(circuits), num_vectors=1220, num_angles=75, shots_per_address=2, seed=0)
    require(np.array_equal(words, after['angle_words']), 'Recovered words do not match the declared table')
    result = verifier.verify(circuits, family / 'submission.npz', tree_edges=after['tree_edges'])
    require(result.get('status') == 'PASS' and result.get('verified_shots') == 78080, 'Full chemistry verification failed')
    require(result.get('num_circuits') == 15 and result.get('toffoli_count') == 14728,
            'Unexpected chemistry resource cost')
    require(abs(result['lambda_eff'] - BUILD['expected_lambda_eff']) < 1e-8, 'Unexpected lambda')
    log('chemistry_verified', score=result['score'], lambda_eff=result['lambda_eff'], shots=result['verified_shots'])
    staged = scratch / 'submission.zip'
    members = package(base, family, staged, dqi_source)
    receipt = {
        'status': 'READY_FOR_KAGGLE_SCORING', 'submission_performed': False,
        'source_notebook': BUILD['source_notebook'], 'source_zip_sha256': sha_file(base),
        'candidate_npz_sha256': BUILD['candidate_npz_sha256'], 'chemistry': result,
        'dqi_source': str(dqi_source), 'dqi_sha256': sha_file(dqi_source),
        'dqi_dataset': BUILD['dqi_dataset'],
        'word_binding': {'all_words_match': True, 'words': 91500, 'shots_per_address': 2},
        'unchanged_tasks': 'Pinned public DQI821 and inverse e46 preserved byte-for-byte; no new DQI/inverse quantum verification run here',
        'members': members, 'submission_zip_sha256': sha_file(staged),
        'submission_zip_bytes': staged.stat().st_size,
        'official_verifier_sha256': sha_file(official / 'verifiers/dfthcsos/verify.py'),
        'official_engine_sha256': sha_file(official / 'kickmix/kickmix.so'),
        'seconds': time.monotonic() - start,
        'score_note': 'This combines pinned public DQI821, inverse e46 and score2 chemistry. Historic27.30683 portfolio identity is not established. Public score remains unknown until scoring.'}
    (output / 'chemistry_full_verification.json').write_text(json.dumps(result, indent=2) + '\n')
    (output / 'submission_v5_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    shutil.copyfile(staged, output / 'submission.zip')
    require(sha_file(output / 'submission.zip') == receipt['submission_zip_sha256'], 'Final ZIP checksum mismatch')
    log('ready', submission_zip_sha256=receipt['submission_zip_sha256'], bytes=receipt['submission_zip_bytes'])


if __name__ == '__main__':
    main()
