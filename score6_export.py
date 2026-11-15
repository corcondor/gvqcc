#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Export the sealed score6 sources, exact evidence, and two small chemistry NPZs.

Only explicit manifest artifacts, selected final root files, and their local
Python source dependencies are included. No broad score6 glob is used: early
orphan discovery files, generated scratch vectors, full DQI KMBs, and portfolio
ZIPs are excluded. This standard-library-only program does not run experiments,
compilers, verification, network requests, or submission commands.

Use --dry-run to inspect an inventory while the final root files are pending.
A real export requires all final files and verifies every manifest-pinned input.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import zipfile
import zlib


MANIFESTS = (
    'score6_invsqrt_manifest.json', 'score6_dqi_mod_manifest.json',
    'score6_dqi_shared11_manifest.json', 'score6_dqi_phase_cache_manifest.json',
    'score6_chem_manifest.json',
)
FINAL_FILES = (
    'score6_dqi_shared11_independent.py', 'score6_dqi_shared11_independent.json',
    'score6_package.py', 'score6_package_receipt.json',
    'score6_scorecard.json', 'score6_results.md',
)
GF8_TENSOR = 'symmetry_dqi_20261115_gf8_joint12_input.txt'
CHEM_PINS = {
    'measured_local_best': '16ee9ad3716309385aa9ce48c1f714e59484b79126ac6fe60591d3ba8bd7ebcf',
    'margin_preserving_alternative': '99627e266340dd5fe71fff264d088024593310e1f06b2b15a61ef6108ee699c0',
}
BASE_CHEM = '5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357'
INVSQRT = '684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a'
DATE = (1980, 1, 1, 0, 0, 0)
MAX_FILE_BYTES = 32 << 20
MAX_TOTAL_BYTES = 64 << 20
ALLOWED_SUFFIXES = {'.py', '.cpp', '.h', '.md', '.json', '.smt2', '.txt',
                    '.kmx', '.kmb', '.npy', '.npz', '.gz'}
MANIFEST_MEMBER = 'EXPORT_MANIFEST.json'
README_MEMBER = 'README.md'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


class Inventory:
    def __init__(self, repo, scratch):
        self.repo = repo.resolve()
        self.scratch = scratch.resolve()
        self.official = self.repo.parent/'official_sources'
        self.verifiers = self.official/'Inzainos/verifiers'
        self.files = {}
        self.missing = []
        self.excluded = []
        self.imports_external = set()

    def resolve(self, value):
        """Resolve historical absolute records or an extracted archive layout."""
        path = Path(value)
        candidates = [path] if path.is_absolute() else [self.repo/path, self.repo.parent/path]
        parts = path.parts
        for marker, root in [('gvqcc_repo', self.repo), ('official_sources', self.official),
                             ('score6_chem', self.repo.parent/'evidence/score6_chem'),
                             ('score6_invsqrt', self.repo.parent/'evidence/score6_invsqrt')]:
            if marker in parts:
                candidates.append(root.joinpath(*parts[parts.index(marker)+1:]))
        for marker in ('score6_chem', 'score6_invsqrt'):
            if marker in parts:
                candidates.append(self.scratch.joinpath(*parts[parts.index(marker):]))
        for candidate in candidates:
            if candidate.is_file():
                return candidate.absolute()
        return candidates[0].absolute()

    def member_name(self, path):
        path = path.absolute()
        if path.is_relative_to(self.repo):
            return 'repo/' + path.relative_to(self.repo).as_posix()
        if path.is_relative_to(self.official):
            return 'official_sources/' + path.relative_to(self.official).as_posix()
        for marker in ('score6_chem', 'score6_invsqrt'):
            if marker in path.parts:
                return 'evidence/' + '/'.join(path.parts[path.parts.index(marker):])
        raise RuntimeError('Source outside the explicit project/evidence roots: ' + str(path))

    def add(self, value, reason, expected_sha=None, expected_bytes=None):
        path = self.resolve(value)
        if not path.is_file():
            self.missing.append({'path': str(path), 'reason': reason})
            return
        require(not path.is_symlink(), 'Refusing a symlink: ' + str(path))
        name = self.member_name(path)
        parts = PurePosixPath(name).parts
        require(not name.startswith('/') and '..' not in parts and
                all(not p.startswith('.') for p in parts), 'Unsafe member name: ' + name)
        require(path.suffix in ALLOWED_SUFFIXES or path.name in {'LICENSE', 'NOTICE'},
                'Unsupported artifact type: ' + str(path))
        require(path.stat().st_size <= MAX_FILE_BYTES, 'Oversized artifact: ' + str(path))
        require(path.name != MANIFEST_MEMBER and path.suffix != '.zip', 'Output/input cycle: ' + name)
        record = self.files.get(name)
        if record:
            require(record['path'] == path, 'Conflicting archive source: ' + name)
            if expected_sha:
                require(record.get('expected_sha256') in (None, expected_sha), 'Conflicting SHA pin: ' + name)
                record['expected_sha256'] = expected_sha
            if expected_bytes is not None:
                require(record.get('expected_bytes') in (None, expected_bytes), 'Conflicting size pin: ' + name)
                record['expected_bytes'] = expected_bytes
            record['reasons'].add(reason)
        else:
            self.files[name] = {'path': path, 'reasons': {reason},
                                'expected_sha256': expected_sha, 'expected_bytes': expected_bytes}

    def pinned(self, record, reason, path=None):
        self.add(path or record['path'], reason, record.get('sha256'), record.get('bytes'))

    def source_dependencies(self):
        """Follow imports without importing/executing the source being packaged."""
        seen = set()
        roots = [self.repo, self.verifiers]
        while True:
            pending = [r['path'] for r in self.files.values()
                       if r['path'].suffix == '.py' and r['path'] not in seen]
            if not pending:
                break
            for source in pending:
                seen.add(source)
                tree = ast.parse(source.read_bytes(), filename=str(source))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        modules = [(a.name, 0) for a in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        modules = [(node.module or '', node.level)]
                        # "from . import helper" is a module import too. An
                        # imported symbol that is not a file is harmless here.
                        if not node.module:
                            modules += [(a.name, node.level) for a in node.names if a.name != '*']
                    else:
                        continue
                    for module, level in modules:
                        bases = [source.parent]
                        if level:
                            bases = [source.parent.joinpath(*(['..']*(level-1))).resolve()]
                        else:
                            bases += roots
                        found = False
                        for base in bases:
                            stem = base.joinpath(*module.split('.')) if module else base
                            alternatives = [stem.with_suffix('.py'), stem/'__init__.py'] if module else [stem/'__init__.py']
                            hit = next((p for p in alternatives if p.is_file()), None)
                            if hit is None:
                                continue
                            if not (hit.is_relative_to(self.repo) or hit.is_relative_to(self.official)):
                                continue
                            self.add(hit, 'Python dependency of ' + self.member_name(source))
                            # Preserve package initializers along the imported
                            # path; namespace packages legitimately have none.
                            parent = hit.parent
                            while parent != base.parent and parent.is_relative_to(base):
                                init = parent/'__init__.py'
                                if init.is_file():
                                    self.add(init, 'Package initializer for ' + module)
                                if parent == base:
                                    break
                                parent = parent.parent
                            found = True
                            break
                        first = module.split('.')[0]
                        if not found and not level and first and first not in sys.stdlib_module_names and first != '__future__':
                            self.imports_external.add(first)

    def snapshot(self):
        blobs, records = {}, []
        for name, item in sorted(self.files.items()):
            path = item['path']; before = path.stat(); raw = path.read_bytes(); after = path.stat()
            require((before.st_ino, before.st_size, before.st_mtime_ns) ==
                    (after.st_ino, after.st_size, after.st_mtime_ns), 'Input changed while reading: ' + str(path))
            require(len(raw) == after.st_size, 'Input size changed: ' + str(path))
            digest = sha(raw)
            require(item['expected_sha256'] in (None, digest), 'Manifest SHA mismatch: ' + name)
            require(item['expected_bytes'] in (None, len(raw)), 'Manifest size mismatch: ' + name)
            if path.suffix == '.json':
                json.loads(raw)
            blobs[name] = raw
            records.append({'name': name, 'source_path': str(path), 'bytes': len(raw),
                            'sha256': digest, 'crc32': f'{zlib.crc32(raw)&0xffffffff:08x}',
                            'reasons': sorted(item['reasons'])})
        require(sum(len(x) for x in blobs.values()) <= MAX_TOTAL_BYTES, 'Evidence bundle exceeded64MiB')
        return blobs, records


def collect(repo, scratch):
    inv = Inventory(repo, scratch)
    documents = {}
    for name in MANIFESTS:
        inv.add(name, 'Explicit authoritative score6 manifest')
        path = inv.resolve(name)
        if path.is_file():
            documents[name] = json.loads(path.read_bytes())
    for name, doc in documents.items():
        for field in ('new_artifacts', 'read_only_dependencies', 'files'):
            for record in doc.get(field, []):
                inv.pinned(record, f'{name}:{field}')
        for filename, record in doc.get('artifacts', {}).items():
            inv.pinned(record, f'{name}:artifacts', filename)
    invsqrt = documents.get('score6_invsqrt_manifest.json')
    if invsqrt:
        require(invsqrt['baseline']['sha256'] == INVSQRT, 'Unexpected inverse-square-root baseline')
        inv.pinned(invsqrt['baseline'], 'Small pinned invsqrt baseline')
        inv.excluded.extend({'path': p, 'reason': 'Generated scratch data, reproducible from included source'}
                            for p in invsqrt.get('scratch_reproducible_paths', []))
    dqi = documents.get('score6_dqi_mod_manifest.json')
    if dqi:
        inv.excluded.append({**dqi['baseline'], 'reason': 'Full522MB DQI is supplied by the score5 portfolio, not this small evidence archive'})
    chem = documents.get('score6_chem_manifest.json')
    if chem:
        require(chem['source_npz_sha256'] == BASE_CHEM, 'Unexpected chemistry baseline')
        require({r['name'] for r in chem['variants']} == set(CHEM_PINS), 'Missing chemistry variant')
        for row in chem['variants']:
            require(row['sha256'] == CHEM_PINS[row['name']], 'Unexpected chemistry candidate SHA')
            inv.pinned(row, 'Exact official-PASS chemistry candidate: ' + row['name'])
            inv.add(row['official_receipt'], 'Exact candidate official receipt', row['official_receipt_sha256'])
        for name in chem['external_dependencies']:
            inv.add(name, 'Explicit chemistry dependency')
    for name in (*FINAL_FILES, GF8_TENSOR, Path(__file__).name):
        inv.add(name, 'Required final root deliverable or exporter')
    fixed = inv.verifiers/'dfthcsos/FeMoCo76o113e.fixed_shifts.npz'
    inv.add(fixed, 'Small official fixed-shift data required by chemistry math')
    for name in ('LICENSE', 'LICENSE.txt', 'NOTICE', 'NOTICE.md'):
        if (inv.repo/name).is_file():
            inv.add(name, 'Existing repository license/notice')
    inv.source_dependencies()
    inv.excluded.append({'name': 'original score5 submission.zip', 'reason': 'External input for the included standalone score6 patcher; no portfolio is embedded'})
    inv.excluded.append({'path': 'official_sources/Inzainos/verifiers/dfthcsos/FeMoCo76o113e.fcidump',
                         'bytes': 128128348,
                         'sha256': 'e5a48af746fd075026dec9e8f5df2d363802a121e8c53af9a0b984bde695e1bd',
                         'reason': 'Large official reference dataset; obtain with the official verifier bundle for new chemistry numerical runs'})
    return inv


def sealed_checks(blobs):
    doc = lambda n: json.loads(blobs['repo/'+n])
    manifest = doc('score6_chem_manifest.json')
    baseline = doc('score6_chem_baseline_verification.json')
    require(baseline['official_result']['status'] == 'PASS', 'Baseline official PASS missing')
    require(baseline['factorization']['sha256'] == BASE_CHEM, 'Baseline receipt SHA differs')
    for row in manifest['variants']:
        receipt = doc(row['official_receipt'])
        require(receipt['official_result']['status'] == 'PASS' and
                receipt['official_result']['verified_shots'] == 78080, 'Incomplete chemistry verification')
        require(receipt['factorization']['sha256'] == row['sha256'] == CHEM_PINS[row['name']], 'Candidate/receipt mismatch')
        require(receipt['official_result'] == row['official_result'], 'Manifest/receipt metrics differ')
        require(receipt['loaders'] == manifest['loader_sha256'], 'Preserved loader SHA list differs')
        require(receipt['official_result']['resources'] == baseline['official_result']['resources'], 'Resource baseline differs')
        require(receipt['baseline_cost'] == baseline['official_result']['score'], 'Comparison cost differs')
        require(receipt['official_result']['score'] < receipt['baseline_cost'], 'No lower chemistry cost')
    # The root controls the schema and contents of the packaging/scorecard
    # receipts. Presence and valid JSON are required, without inventing a
    # new official-verification or public-score claim here.
    doc('score6_package_receipt.json'); doc('score6_scorecard.json')


def readme():
    return b"""# Score6 sources and exact evidence

This archive contains the five explicit score6 evidence manifests, their
listed bounded artifacts, recursively resolved local Python source modules,
the source GF8 tensor, and both official-PASS chemistry NPZ candidates. The
top-level EXPORT_MANIFEST.json gives all payload SHA256/CRC values. The separate
external receipt binds the final archive SHA256 and checks every member.

Start with repo/score6_results.md and repo/score6_scorecard.json. The standalone
repo/score6_package.py takes the original score5 submission ZIP as external
input. This evidence archive intentionally contains neither that portfolio nor
the522MB DQI circuit. The selected chemistry endpoint and the margin-preserving
alternative are under evidence/score6_chem/. No new submission was performed
by this exporter.

The research scripts retain their recorded defaults; use their explicit path
arguments when replaying elsewhere. Scientific experiments need the recorded
NumPy/SciPy/SymPy/Z3/KickMix environment as applicable. A new chemistry numerical
run also needs the official128MB FeMoCo reference FCIDUMP, whose expected hash
is recorded in EXPORT_MANIFEST.json. Packaging the accepted byte-pinned NPZ
does not need that dataset or a new numerical run.

The inverse-square-root small positive-control circuit is a demonstration,
not a new accepted benchmark circuit. The shared11 SAT result is scoped to its
fixed tensor encoding; see its report for the lack of an independently checked
UNSAT proof object. No unqualified global optimality claim is made.

Early orphan phase-discovery outputs and large generated scratch vectors are
not included. Only explicit authoritative artifacts and dependency sources
were collected. ZIP entries are sorted, dated1980-01-01, regular0644 files,
and ZIP_STORED to make output independent of zlib compressor versions. The
internal manifest excludes itself to avoid a hash cycle. The external receipt
contains the hashes of all archive members, including that manifest.
"""


def publish(path, raw):
    with path.open('xb') as f:
        f.write(raw)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--scratch', type=Path, default=Path('/workspace/scratch/3815fb5fae06'))
    p.add_argument('--output', type=Path, default=Path('/workspace/scratch/3815fb5fae06/score6_delivery/score6_sources_and_evidence.zip'))
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--inventory', type=Path, help='Optional dry-run inventory JSON; never overwritten')
    a = p.parse_args()
    inv = collect(a.repo, a.scratch)
    blobs, rows = inv.snapshot()
    inventory = {'status': 'READY' if not inv.missing else 'WAITING_FOR_REQUIRED_FILES',
                 'source_file_count': len(rows), 'source_bytes': sum(r['bytes'] for r in rows),
                 'missing': inv.missing, 'files': rows,
                 'repo_files': [dict(path=r['name'].removeprefix('repo/'),
                                     bytes=r['bytes'], sha256=r['sha256'], source_path=r['source_path'])
                                for r in rows if r['name'].startswith('repo/')],
                 'external_python_packages': sorted(inv.imports_external), 'excluded_external_inputs': inv.excluded}
    receipt_names = {'repo/score6_package_receipt.json', 'repo/score6_scorecard.json',
                     'repo/score6_chem_manifest.json', 'repo/score6_chem_baseline_verification.json',
                     'repo/score6_chem_transfer_full_verification.json', 'repo/score6_chem_backoff_full_verification.json'}
    if receipt_names <= blobs.keys():
        sealed_checks(blobs)
        inventory['receipt_bindings'] = 'PASS'
    else:
        inventory['receipt_bindings'] = 'PENDING_REQUIRED_RECEIPTS'
    if a.dry_run:
        if a.inventory:
            a.inventory.parent.mkdir(parents=True, exist_ok=True)
            publish(a.inventory, encoded(inventory))
        print(json.dumps({k:v for k,v in inventory.items() if k not in {'files','repo_files','excluded_external_inputs'}}, indent=2))
        return
    require(not inv.missing, 'Required final files are missing: ' + json.dumps(inv.missing))
    sealed_checks(blobs)
    output = a.output.absolute()
    manifest_path = output.with_suffix('.manifest.json')
    receipt_path = output.with_suffix('.receipt.json')
    for path in (output, manifest_path, receipt_path):
        require(not path.exists(), 'Refusing to replace an existing export: ' + str(path))
    require(all(output != record['path'] for record in inv.files.values()), 'Output is an input')
    output.parent.mkdir(parents=True, exist_ok=True)
    blobs[README_MEMBER] = readme()
    generated = {'name': README_MEMBER, 'bytes': len(blobs[README_MEMBER]), 'sha256': sha(blobs[README_MEMBER]),
                 'crc32': f'{zlib.crc32(blobs[README_MEMBER])&0xffffffff:08x}', 'reasons': ['Generated archive guide']}
    # Runtime source locations are useful in the external dry-run inventory,
    # but do not belong in a content-reproducible internal archive manifest.
    payload_rows = [{k:v for k,v in row.items() if k != 'source_path'} for row in rows]
    manifest = {'schema': 'score6-source-evidence-export-v1',
                'status': 'SEALED_INPUT_HASHES_AND_OFFICIAL_CHEMISTRY_RECEIPTS_CHECKED',
                'members': sorted(payload_rows+[generated], key=lambda x:x['name']),
                'repo_files': [dict(path=r['name'].removeprefix('repo/'), bytes=r['bytes'], sha256=r['sha256'])
                               for r in rows if r['name'].startswith('repo/')],
                'payload_file_count': len(blobs), 'payload_bytes': sum(map(len, blobs.values())),
                'zip_format': {'compression': 'ZIP_STORED', 'date_time': list(DATE), 'mode': '0100644', 'sort': 'member name'},
                'manifest_self_exclusion': 'The manifest does not list its own hash. The external receipt lists every member and the archive SHA.',
                'external_python_packages': sorted(inv.imports_external),
                'excluded_external_inputs': inv.excluded,
                'simulator_or_verifier_invoked': False, 'submission_performed': False}
    raw_manifest = encoded(manifest)
    blobs[MANIFEST_MEMBER] = raw_manifest
    with tempfile.TemporaryDirectory(prefix='score6_export_', dir=output.parent) as td:
        temporary = Path(td)/'archive.zip'
        with zipfile.ZipFile(temporary, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
            for name, raw in sorted(blobs.items()):
                info = zipfile.ZipInfo(name, DATE)
                info.create_system = 3; info.external_attr = (stat.S_IFREG|0o644)<<16
                info.compress_type = zipfile.ZIP_STORED; info.extra = b''; info.comment = b''
                z.writestr(info, raw)
        checked = []
        with zipfile.ZipFile(temporary) as z:
            require(z.namelist() == sorted(blobs), 'Duplicate, missing, or unsorted member')
            require(z.testzip() is None, 'ZIP CRC failure')
            for info in z.infolist():
                raw = z.read(info.filename)
                require(raw == blobs[info.filename], 'Member bytes differ: ' + info.filename)
                require(info.CRC == (zlib.crc32(raw)&0xffffffff), 'Member CRC differs')
                require(info.date_time == DATE and info.compress_type == zipfile.ZIP_STORED and
                        info.create_system == 3 and info.external_attr == (stat.S_IFREG|0o644)<<16,
                        'Noncanonical ZIP metadata')
                checked.append({'name': info.filename, 'bytes': len(raw), 'sha256': sha(raw),
                                'crc32': f'{info.CRC:08x}', 'sha256_pass': True, 'crc_pass': True})
        # Protect against agents changing a source while the archive was made.
        for name, item in inv.files.items():
            require(item['path'].read_bytes() == blobs[name], 'Source changed during export: ' + name)
        archive_raw = temporary.read_bytes()
        receipt = {'schema': 'score6-source-evidence-export-receipt-v1', 'status': 'PACKAGE_INTEGRITY_PASS',
                   'archive': str(output), 'archive_sha256': sha(archive_raw), 'archive_bytes': len(archive_raw),
                   'member_count': len(checked), 'all_member_sha256_and_crc_pass': True,
                   'source_files_unchanged_during_export': True, 'deterministic_metadata_checked': True,
                   'manifest': str(manifest_path), 'manifest_sha256': sha(raw_manifest), 'members': checked,
                   'full_DQI_embedded': False, 'original_portfolio_embedded': False,
                   'exporter_sha256': sha(Path(__file__).read_bytes()),
                   'new_verification_run': False, 'new_submission': False}
        # Hard-link publication is atomic and fails if a competing writer has
        # already created the requested output; no existing file is replaced.
        os.link(temporary, output)
        publish(manifest_path, raw_manifest)
        publish(receipt_path, encoded(receipt))
    print(json.dumps({k:v for k,v in receipt.items() if k!='members'}, indent=2))


if __name__ == '__main__':
    main()
