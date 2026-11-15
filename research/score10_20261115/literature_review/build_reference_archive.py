"""Package original reading notes and code, excluding third-party paper bodies."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'deliverables'

FILES = [
    'deliverables/reference_review.json',
    'deliverables/reference_review.md',
    'deliverables/reading_counts.json',
    'deliverables/LITERATURE_FINDINGS_JA.md',
    'deliverables/README_REFERENCES_JA.md',
    'literature/main_references.json',
    'literature/main_references.md',
    'literature/main_paper_notes_ja.md',
    'literature/findings_template.md',
    'literature/refs_01_25.json',
    'literature/refs_01_25.md',
    'literature/refs26_43/reading_ledger.json',
    'literature/refs26_43/reading_ledger_ja.md',
    'literature/refs26_43/ref39_read_scope.json',
    'literature/refs_44_61_and_v1_only.json',
    'literature/refs_44_61_and_v1_only.md',
    'literature/root_reference_supplement.json',
    'literature/root_reference_supplement.md',
    'literature/root_reference_supplement_additional_entries.json',
    'literature/root_reference_supplement_cost.json',
    'literature/root_reference_supplement_cost.md',
    'literature/shallow_final_supplement.json',
    'literature/shallow_final_supplement.md',
    'literature/shallow_root_final_supplement.json',
    'literature/shallow_root_final_supplement.md',
    'literature/cost_audit_supplement/reading_ledger.json',
    'literature/cost_audit_supplement/reading_ledger_ja.md',
    'literature/cost_audit_supplement/ref49_zero_input_identifiability_check.json',
    'literature/linked_sources/magic_bibliography.json',
    'literature/linked_sources/magic_bibliography.md',
    'literature/linked_sources/graphene_bibliography.json',
    'literature/linked_sources/graphene_bibliography.md',
    'literature/linked_sources/magic_coverage.json',
    'literature/linked_sources/magic_coverage.md',
    'literature/linked_sources/magic_coverage_manifest.json',
    'literature/linked_sources/magic_document_presence_audit.json',
    'literature/linked_sources/magic_notes_ja.json',
    'literature/linked_sources/magic_reference_notes.json',
    'literature/linked_sources/magic_version_comparison.json',
    'literature/linked_sources/ref52_identity_evidence.json',
    'literature/linked_sources/linked_source_report.md',
    'literature/magic_ref_31_review.json',
    'literature/magic_ref_31_review.md',
    'literature/magic44_53/reading_ledger.json',
    'literature/magic44_53/reading_ledger_ja.md',
    'literature/magic44_53/ref44_reading.md',
    'literature/magic44_53/ref50_algebra_checks.json',
    'literature/graphene_refs_01_28.json',
    'literature/graphene_refs_01_28.md',
    'literature/graphene_refs_29_56.json',
    'literature/graphene_refs_29_56.md',
    'literature/graphene_supplement_29_42.json',
    'literature/graphene_supplement_29_42.md',
    'literature/graphene_supplement_43_56.json',
    'literature/graphene_supplement_43_56.md',
    'literature/ccz_figure3_resource_check.json',
    'literature/native_ccz.kmb',
    'literature/seven_t_depth_one.kmb',
    'build_reference_archive.py',
]


def main():
    data = json.loads((OUT / 'reference_review.json').read_text())
    rows = data['references']
    assert len(rows) == len({r['id'] for r in rows}) == 171
    for r in rows:
        assert r['primary_urls'] and r['result'] and r['applicability'], r['id']
        assert r['review_status'] not in {'selected_sections', 'main_results_reviewed', 'bibliography_only'}, r['id']
    paths = {ROOT / name for name in FILES}
    # These are original scripts only; all paper text, PDF and image caches are excluded.
    paths.update((ROOT / 'literature').rglob('*.py'))
    paths.update((ROOT / 'literature/root_refs').glob('read_pass*.json'))
    for p in paths:
        assert p.is_file(), p
        assert p.suffix in {'.py', '.md', '.json', '.kmb'}, p
    records = [
        {'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
         'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(paths)
    ]
    manifest = {
        'date': '2026-11-15',
        'bibliographic_entry_count': 171,
        'reading_counts': data['metadata']['counts_total'],
        'scope': 'Original analysis, bibliographic facts, primary-source URLs, actual reading scopes and hashes, and original code. No third-party paper bodies or page images.',
        'reading_limit': data['metadata']['limits'],
        'files': records,
    }
    payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    (OUT / 'reference_review_manifest.json').write_bytes(payload)
    archive = OUT / 'reference_review.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(paths):
            info = zipfile.ZipInfo(p.relative_to(ROOT).as_posix(), date_time=(2026, 11, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes())
        info = zipfile.ZipInfo('reference_review_manifest.json', date_time=(2026, 11, 15, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, payload)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for r in records:
            b = z.read(r['path'])
            assert len(b) == r['bytes'] and hashlib.sha256(b).hexdigest() == r['sha256']
    b = archive.read_bytes()
    receipt = {
        'archive': archive.name, 'bytes': len(b),
        'sha256': hashlib.sha256(b).hexdigest(),
        'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest(),
        'file_count': len(records),
        'manifest_sha256': hashlib.sha256(payload).hexdigest(),
        'all_archive_entries_verified': True,
    }
    (OUT / 'reference_archive_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
