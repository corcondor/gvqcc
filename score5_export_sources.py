#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Deterministically export score5 sources and bounded evidence after sealing.

This uses only the Python standard library. --dry-run writes no archive and
can emit a repo-relative inventory for Git persistence while final receipts
are pending. A real export requires the qualified e4 worker and packaging
receipt. It never invokes a compiler, simulator, network, or verifier.
"""
from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import zipfile

FINAL = 'e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355'
DATE_TIME = (1980, 1, 1, 0, 0, 0)
LIMIT = 32 << 20
TEXT_SUFFIXES = {'.py', '.cpp', '.md', '.json'}
CORE = (
    'dqi_ccx_peephole.py', 'kmb_profile.py', 'kmb_splice.py',
    'score4_measurement_fanout.py', 'score4_dqi_guard_review.py',
    'score4_hmr_hoist.py', 'verify_dqi_candidate.py',
    'score3_submission_manifest.json', 'score4_dqi_full_verification.json',
    'outcome_dqi_chart_inverse_norm.py', 'outcome_dqi_chart_third_norm.py',
    'outcome_dqi_chart_check_norm.py', 'outcome_dqi_chart_splice_norm.py',
    'outcome_dqi_chart_match.py', 'outcome_dqi_chart_paired.py',
    'outcome_dqi_chart_paired.json', 'outcome_dqi_chart_paired_plan.json',
    'outcome_dqi_chart_paired_comparison.json',
    'score3_chemistry_multistep_transport.py', 'dqi_rare_failure_admission.json',
)
NORM_REQUIRED = (
    'outcome_dqi_chart_norm_worker.py', 'outcome_dqi_chart_norm_worker_template.py',
    'outcome_dqi_chart_norm_patch.json.gz', 'outcome_dqi_chart_norm_proof.md',
    'outcome_dqi_chart_norm_qualification_binding.json',
    'outcome_dqi_chart_norm_qualification_scope.json',
    'outcome_dqi_chart_norm_paired.json', 'outcome_dqi_chart_norm_paired_plan.json',
    'outcome_dqi_chart_norm_paired_comparison.json',
    'outcome_dqi_chart_norm_full_verification.json',
    'outcome_dqi_chart_norm_LICENSE.txt', 'outcome_dqi_chart_norm_NOTICE.md',
)
FINAL_FILES = (
    'score5_dqi_final_full_verification.json', 'score5_final_worker.py',
    'score5_final_worker_template.py', 'score5_final_worker_build.py',
    'score5_final_worker_manifest.json', 'score5_final_worker_build.json',
    'score5_final_worker_check.json', 'score5_final_worker_hmr_recipe.json',
    'score5_final_worker_hmr_patch.json.gz', 'score5_final_worker_README.md',
)
EVIDENCE = {
    'score5_norm_fanout': ('before_profile.json', 'after_profile.json',
                          'patch.json', 'rewrite_certificate.json'),
    'score5_norm_fanout_fanin': ('profile.json', 'patch.json', 'rewrite_certificate.json'),
    'score5_norm_final': ('profile.json', 'patch.json', 'rewrite_certificate.json'),
}
WIDTH_FILES = ('component.json',) + tuple(
    f'borrow{n}_{kind}.kmb' for n in (0, 1, 6) for kind in ('pair', 'chart'))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def canonical(value):
    return json.dumps(value, separators=(',', ':'), sort_keys=True).encode()


def imported_modules(raw, name):
    tree = ast.parse(raw, filename=name)
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(a.name.split('.')[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            modules.add(node.module.split('.')[0])
    return modules


def collect(repo, scratch):
    files, missing = {}, []

    def add(path, name, required=True):
        if not path.is_file():
            if required:
                missing.append(name)
            return
        require(not path.is_symlink(), 'Refusing a symlink: ' + str(path))
        require(path.stat().st_size <= LIMIT, 'Oversized evidence file: ' + str(path))
        require(name not in files or files[name] == path, 'Archive name collision: ' + name)
        files[name] = path

    for path in sorted(repo.glob('score5_*')):
        if path.suffix in TEXT_SUFFIXES or path.name.endswith('.json.gz'):
            add(path, 'repo/' + path.name)
    for name in (*CORE, *NORM_REQUIRED, *FINAL_FILES):
        add(repo/name, 'repo/' + name)
    # Includes the portable norm worker, embedded patch, licenses, proof,
    # qualification binding, paired receipts, review, and build receipts.
    for path in sorted(repo.glob('outcome_dqi_chart_norm*')):
        if path.suffix in TEXT_SUFFIXES | {'.txt'} or path.name.endswith('.json.gz'):
            add(path, 'repo/' + path.name)
    for group, required in EVIDENCE.items():
        directory = scratch/group
        for name in required:
            add(directory/name, 'evidence/' + group + '/' + name)
        for path in sorted(directory.glob('*.json')):
            add(path, 'evidence/' + group + '/' + path.name)
    for name in WIDTH_FILES:
        add(scratch/'score5_dqi_width/component'/name,
            'evidence/score5_dqi_width/component/' + name)

    # Follow all statically imported repository-local Python modules. External
    # Apache source modules and installed packages are separately disclosed.
    local = {p.stem: p for p in repo.glob('*.py')}
    visited, external = set(), set()
    pending = [p for n, p in files.items() if n.startswith('repo/') and p.suffix == '.py']
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        for name in imported_modules(path.read_bytes(), path.name):
            if name in local:
                other = local[name]
                add(other, 'repo/' + other.name)
                if other not in visited:
                    pending.append(other)
            elif name not in sys.stdlib_module_names and name != '__future__':
                external.add(name)
    return dict(sorted(files.items())), sorted(set(missing)), sorted(external)


def snapshot(files):
    data = {}
    for name, path in files.items():
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
        require((before.st_ino, before.st_size, before.st_mtime_ns) ==
                (after.st_ino, after.st_size, after.st_mtime_ns),
                'Source changed while reading: ' + str(path))
        require(len(raw) == after.st_size, 'Source size changed: ' + str(path))
        if name.endswith('.json'):
            json.loads(raw)
        data[name] = raw
    return data


def sealed_checks(data):
    def blob(name):
        return data['repo/' + name]
    def doc(name):
        return json.loads(blob(name))
    qbytes = blob('score5_dqi_final_full_verification.json')
    q = json.loads(qbytes)
    require(q['status'] == 'PASS' and q['circuit_sha256'] == FINAL, 'Final official PASS missing')
    require(q['verified_shots'] == 102400 and q['value_errors'] == q['phase_errors'] == 0,
            'Final verification coverage/errors differ')
    require(q['seed'] is None and q['salt'] == '' and q['log2_delta'] == -128,
            'Final official default sampling differs')
    build = doc('score5_final_worker_build.json')
    check = doc('score5_final_worker_check.json')
    require(build['candidate_sha256'] == check['candidate_dqi_sha256'] == FINAL, 'Final worker target differs')
    require(build['worker_sha256'] == digest(blob('score5_final_worker.py')), 'Final worker SHA differs')
    require(build['builder_sha256'] == digest(blob('score5_final_worker_build.py')), 'Final builder changed')
    require(build['template_sha256'] == digest(blob('score5_final_worker_template.py')), 'Final template changed')
    require(build['hmr_patch_gzip_sha256'] == digest(blob('score5_final_worker_hmr_patch.json.gz')),
            'Final gzip patch differs from build receipt')
    require(blob('score5_final_worker_hmr_recipe.json') == data['evidence/score5_norm_final/patch.json'],
            'Final copied operation recipe differs from full evidence')
    require(build['official_receipt_sha256'] == check['official_dqi_receipt_sha256'] == digest(qbytes),
            'Final worker/receipt binding differs')
    require(check['status'] == 'PACKAGE_INTEGRITY_PASS' and check['member_count'] == 18 and
            check['all_member_sha256_and_crc_pass'] and check['preserved_non_dqi_members'] == 17,
            'Final portfolio packaging receipt is incomplete')
    retained = {r['name']: r for r in doc('score3_submission_manifest.json')['members']}
    require(set(retained) == set(check['members']), 'Portfolio member set differs')
    for name, row in check['members'].items():
        require(row['sha256_pass'] and row['crc_pass'], 'Portfolio member failed: ' + name)
        require(row['sha256'] == (FINAL if name == 'dqi.kmb' else retained[name]['sha256']),
                'Unexpected portfolio member bytes: ' + name)

    # Parse the standalone worker's embedded data; never execute the worker.
    constants = {}
    worker = blob('score5_final_worker.py')
    require(not (imported_modules(worker, 'score5_final_worker.py') -
                 sys.stdlib_module_names - {'__future__'}), 'Final worker has non-stdlib imports')
    for node in ast.parse(worker).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ('PAYLOAD_B64', 'PAYLOAD_SHA256'):
                constants[node.targets[0].id] = ast.literal_eval(node.value)
    raw = gzip.decompress(base64.b64decode(constants['PAYLOAD_B64'], validate=True))
    require(digest(raw) == constants['PAYLOAD_SHA256'] == build['payload_raw_sha256'], 'Worker payload SHA differs')
    payload = json.loads(raw)
    manifest_raw = blob('score5_final_worker_manifest.json')
    require(base64.b64decode(payload['manifest_bytes_b64'], validate=True) == manifest_raw,
            'Embedded worker manifest differs')
    require(digest(manifest_raw) == payload['manifest_sha256'] == check['manifest_sha256'],
            'Worker manifest SHA differs')
    require(base64.b64decode(payload['official_receipts_b64'][FINAL], validate=True) == qbytes,
            'Embedded final receipt differs')
    manifest = json.loads(manifest_raw)
    require(payload['manifest'] == manifest, 'Embedded manifest objects differ')
    require(manifest['targets'][manifest['default_target']]['sha256'] == FINAL, 'Wrong default target')
    require(len(payload['patches']) == len(manifest['stages']), 'Worker patch count differs')
    for patch, stage in zip(payload['patches'], manifest['stages']):
        require(digest(canonical(patch)) == stage['patch_sha256'], 'Embedded patch SHA differs')
    width = json.loads(data['evidence/score5_dqi_width/component/component.json'])
    for variant in width['variants']:
        for record in (variant, variant['chart_template']):
            key = 'evidence/score5_dqi_width/component/' + Path(record['path']).name
            require(digest(data[key]) == record['sha256'], 'Native width component SHA differs: ' + key)
    final_patch = json.loads(data['evidence/score5_norm_final/patch.json'])
    final_profile = json.loads(data['evidence/score5_norm_final/profile.json'])
    require(final_patch['candidate_sha256'] == final_profile['raw_kmb_sha256'] == FINAL,
            'Final full patch/profile differ')
    return {'final_dqi_sha256': FINAL, 'final_official_receipt_sha256': digest(qbytes),
            'final_worker_sha256': build['worker_sha256'],
            'qualified_submission_sha256': check['output_sha256'],
            'worker_stdlib_only': True, 'native_width_component_hashes_checked': 6,
            'scientific_verifier_rerun': False}


def source_readme(external):
    return ('''# Score5 source and evidence export

This is a source/evidence archive, not an 18-member competition submission.
The final standalone reconstruction entry point is `repo/score5_final_worker.py`.
It uses Python's standard library and embeds the complete SHA-bound patch chain,
licenses, and official receipt. It requires a supported predecessor portfolio
ZIP or DQI KMB. Run it with `--help`; it performs no network access or submission.

All `repo/score5_*.py/.cpp/.md/.json` files present at sealing are included,
along with gzip patch payloads, recursive repo-local Python dependencies,
the chart repair's sources/proof/qualification/paired evidence, and predecessor
scorecard receipts. Full certificates, operation recipes, and binary profiles
for all three score5 stages are under `evidence/`. The six small native width
fixtures are included and bound to their original component receipt.

Research experiments additionally need the public Apache-2.0 source tree under
`official_sources/Syed_v12/source/dqi_source/src/controller_work`, the unchanged
official verifier tree under `official_sources/Inzainos/verifiers`, KickMix,
and where applicable NumPy/SciPy and pinned chemistry input data. Those external
trees, predecessor/full 500-MB DQI KMBs, full submission ZIPs, large data arrays,
and caches are deliberately not copied. Existing source paths and hashes are
retained in the individual reports. The source files retain their original
credits; the chart LICENSE and NOTICE are included verbatim.

The exporter checks receipt/payload/file integrity, not quantum correctness.
Local finite official PASS is not universal correctness; the documented node13
numerator-zero failure and all research-only width caveats remain in force.
No public score improvement or new submission is claimed by this archive.

`MANIFEST.json` hashes every other member. Its own SHA and the complete archive
SHA are in the external export receipt. Names are sorted, timestamps fixed to
1980-01-01, permissions fixed to regular0644, and ZIP_STORED is used so compressor
version differences cannot change the bytes. Files changing during assembly
cause an error. No timestamp or machine-specific build metadata is embedded.

Non-stdlib imports in the research source closure:

''' + '\n'.join('- `' + name + '`' for name in external) + '\n').encode()


def publish_bytes(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.score5-export-', dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(raw)
        os.link(temp, path)  # atomic publication; refuses to overwrite
    finally:
        temp.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument('--scratch', type=Path, default=Path('/workspace/scratch/3815fb5fae06'))
    ap.add_argument('--output', type=Path, help='New source/evidence ZIP, outside the repository')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--inventory-json', type=Path, help='Write the dry-run inventory to a new external JSON file')
    a = ap.parse_args()
    repo, scratch = a.repo.resolve(), a.scratch.resolve()
    files, missing, external = collect(repo, scratch)
    data = snapshot(files)
    rows = [{'name': n, 'bytes': len(raw), 'sha256': digest(raw)} for n, raw in sorted(data.items())]
    inventory = {'status': 'INVENTORY_ONLY_NO_ARCHIVE', 'member_count_without_generated_metadata': len(rows),
                 'material_bytes': sum(x['bytes'] for x in rows), 'missing_required': missing,
                 'repo_files': [dict(path=x['name'][5:], bytes=x['bytes'], sha256=x['sha256'])
                                for x in rows if x['name'].startswith('repo/')],
                 'evidence_files': [x for x in rows if x['name'].startswith('evidence/')],
                 'external_research_imports': external}
    if a.dry_run:
        if a.inventory_json:
            require(not a.inventory_json.resolve().is_relative_to(repo), 'Inventory must be outside repo')
            publish_bytes(a.inventory_json.resolve(), json_bytes(inventory))
        print(json.dumps({k: v for k, v in inventory.items() if k not in ('repo_files', 'evidence_files')}, indent=2))
        return
    require(a.output is not None, '--output is required unless --dry-run is used')
    require(not missing, 'Required sources/evidence are not sealed: ' + ', '.join(missing))
    output = a.output.resolve()
    require(not output.is_relative_to(repo), 'Export outputs must be outside repository')
    manifest_path = output.with_suffix('.manifest.json')
    receipt_path = output.with_suffix('.receipt.json')
    require(not any(p.exists() for p in (output, manifest_path, receipt_path)), 'Export destination already exists')
    binding = sealed_checks(data)
    data['README.md'] = source_readme(external)
    manifest = {'schema': 'gvqcc-score5-source-evidence-export-v1', 'binding': binding,
                'members': [{'name': n, 'bytes': len(raw), 'sha256': digest(raw)}
                            for n, raw in sorted(data.items())],
                'manifest_excludes_itself': True, 'compression': 'ZIP_STORED',
                'timestamp': list(DATE_TIME), 'permissions': 'regular0644',
                'external_research_imports': external}
    manifest_raw = json_bytes(manifest)
    data['MANIFEST.json'] = manifest_raw
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.score5-export-', suffix='.zip', dir=output.parent)
    os.close(fd)
    temp = Path(name)
    try:
        with zipfile.ZipFile(temp, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
            for member, raw in sorted(data.items()):
                info = zipfile.ZipInfo(member, DATE_TIME)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_STORED
                z.writestr(info, raw)
        with zipfile.ZipFile(temp) as z:
            require(z.namelist() == sorted(data), 'ZIP member order differs')
            require(z.testzip() is None, 'Archive CRC verification failed')
            for member, raw in data.items():
                require(digest(z.read(member)) == digest(raw), 'Archive member SHA differs: ' + member)
        for member, path in files.items():
            require(path.read_bytes() == data[member], 'Source changed during export: ' + str(path))
        archive_sha = digest(temp.read_bytes())
        archive_bytes = temp.stat().st_size
        os.link(temp, output)
    finally:
        temp.unlink(missing_ok=True)
    publish_bytes(manifest_path, manifest_raw)
    receipt = {'status': 'SOURCE_EVIDENCE_ARCHIVE_INTEGRITY_PASS', 'archive_sha256': archive_sha,
               'archive_bytes': archive_bytes, 'archive_name': output.name,
               'manifest_sha256': digest(manifest_raw), 'member_count': len(data),
               'all_member_sha256_and_crc_pass': True, 'source_bytes_unchanged': True,
               'binding': binding, 'new_scientific_tests': False,
               'repo_files': inventory['repo_files'], 'evidence_files': inventory['evidence_files']}
    publish_bytes(receipt_path, json_bytes(receipt))
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('repo_files', 'evidence_files')}, indent=2))


if __name__ == '__main__':
    main()
