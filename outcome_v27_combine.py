#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Package pinned v27 chemistry/invsqrt with the qualified 9a82 DQI.

Attach notebook outputs from maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry
v3 (or its exact copy) and geocpuresearch/gvqcc-exact4096-gauge-score2 v1.
CPU, standard library only, no network or credentials. This does not submit.
It verifies byte identity and archive integrity; it does not rerun simulation.
"""
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import zipfile

PUBLIC = json.loads('{\n  "upstream_notebook": "maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry",\n  "script_version_id": 369706978,\n  "observed_public_score": 27.31512,\n  "observed_upstream_official_results": {\n    "dfthcsos_cost": 294888332.1042627,\n    "dqi_cost": 360209905486.0156,\n    "invsqrt_cost": 78673.56921101942,\n    "statuses": [\n      "PASS",\n      "PASS",\n      "PASS"\n    ]\n  },\n  "license_note": "Notebook Apache-2.0; chemistry CC0; other circuits retain upstream terms. Exact credit text is preserved in upstream notebook.",\n  "members": {\n    "invsqrt.kmb": {\n      "sha256": "1ba197b027713aac164056d12505c87f286c3fcd94f403c522073325763bf2f9",\n      "bytes": 198631\n    },\n    "dqi.kmb": {\n      "sha256": "821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3",\n      "bytes": 455584321\n    },\n    "dfthcsos/submission.npz": {\n      "sha256": "4df35abdeec320a3f1c10f6f533e73550e50bb45d95e666deaa01062810a3559",\n      "bytes": 1847692\n    },\n    "dfthcsos/angle_k_0.kmb": {\n      "sha256": "71735b23037e8a64d16e39b3347d440b36bdf8813613ec70c36a85bfd362d7c2",\n      "bytes": 410442\n    },\n    "dfthcsos/angle_k_1.kmb": {\n      "sha256": "1a43bbc368785aa5fc5210f6e4d5d2f9ddf114f7f3f6d3e3964f9478056bb4be",\n      "bytes": 420614\n    },\n    "dfthcsos/angle_k_2.kmb": {\n      "sha256": "0970b392fb4bed09d6026b77b4b31510573123cb76955030115507bffde4a6bb",\n      "bytes": 418801\n    },\n    "dfthcsos/angle_k_3.kmb": {\n      "sha256": "f9d313326dd07028bf6ef672bb47013f01e9311695d66b8d1ee2546d7dbacd7f",\n      "bytes": 421008\n    },\n    "dfthcsos/angle_k_4.kmb": {\n      "sha256": "0ab29f06e44ef247035c971dcca30e27616bdfdc2a102fbb58c3882bbfbfd1e0",\n      "bytes": 347635\n    },\n    "dfthcsos/angle_k_5.kmb": {\n      "sha256": "b346df2edafbaf4d95192a974db27abf71b770f51ee61dae2eb352f422cefdf4",\n      "bytes": 351040\n    },\n    "dfthcsos/angle_k_6.kmb": {\n      "sha256": "749d9edb817c59f8a3507400002e75c2d8db55932a6933db5c5f6f59a2679f7b",\n      "bytes": 347703\n    },\n    "dfthcsos/angle_k_7.kmb": {\n      "sha256": "0ad7d3775a36d7c14e3d4dfa4a144267e4e9759521fae4022715be25c309638e",\n      "bytes": 350049\n    },\n    "dfthcsos/angle_k_8.kmb": {\n      "sha256": "46e0f8d69e532438d476aa8244f257a649fdc4cffe9d41f9921758f4dc18fa83",\n      "bytes": 346523\n    },\n    "dfthcsos/angle_k_9.kmb": {\n      "sha256": "0b995537e919351a705babb6294dfe3525ef52a3c40b08122d842f45df8182da",\n      "bytes": 354023\n    },\n    "dfthcsos/angle_k_10.kmb": {\n      "sha256": "5fea9f297afea7ffe74054ed1b44f92031a5f6e319a7f1c8741f86c05b234834",\n      "bytes": 347748\n    },\n    "dfthcsos/angle_k_11.kmb": {\n      "sha256": "dc425931348cc4950931c400ab19322e01495b7cf3e2d02bafabcaaf9559d28a",\n      "bytes": 350356\n    },\n    "dfthcsos/angle_k_12.kmb": {\n      "sha256": "64bbada35a382068b8dfbca0df0d781df8704aa367882cc426b76e2767f3d13f",\n      "bytes": 348617\n    },\n    "dfthcsos/angle_k_13.kmb": {\n      "sha256": "958789349187a70ab3baf426655aacd2360113f71ab9a7b49d6624bd0e20bcd6",\n      "bytes": 344270\n    },\n    "dfthcsos/angle_k_14.kmb": {\n      "sha256": "f35c803dece96ceb0ba24040e7c232a73170a3692c4f5212bdeadcbfcd154212",\n      "bytes": 352571\n    }\n  }\n}\n')
QUALIFICATION_B64 = 'ewogICJzdGF0dXMiOiAiUEFTUyIsCiAgInNjb3JlIjogMzU5NzM0NzQ1Nzc4Ljk4NzYsCiAgIm0iOiA0MDk1LAogICJuIjogNzAsCiAgImRlZ3JlZSI6IDEyLAogICJyIjogMjAxNiwKICAidmVyaWZpZWRfc2hvdHMiOiAxMDI0MDAsCiAgInZhbHVlX2Vycm9ycyI6IDAsCiAgInBoYXNlX2Vycm9ycyI6IDAsCiAgImVtcGlyaWNhbF9lcnJvcl9yYXRlIjogMC4wLAogICJlZmZlY3RpdmVfZXJyb3JfcmF0ZSI6IDAuMDAwODY2MDU4NzMwMTY1NzkyNiwKICAibG9nMl9kZWx0YSI6IC0xMjguMCwKICAicmVwZXRpdGlvbl9mYWN0b3IiOiAxLjE5MTI2MDQ2NDgxMTU4MzIsCiAgIm1lYW5fZXJyb3Jfd2VpZ2h0IjogMzEuMDQ2NzM3MzMxNzQ2NjM0LAogICJ0b2Zmb2xpX2NvdW50IjogMzgyMDk1LjY4Nzc5Mjk2ODc2LAogICJtYXhfdG9mZm9saV9jb3VudCI6IDM4MjkzNCwKICAicmVhY3Rpb25fZGVwdGgiOiA0MDg5MSwKICAibnVtX29wcyI6IDU4ODY5MDQyLAogICJzaG90X29wZXJhdGlvbl9jb3VudHMiOiB7CiAgICAiQklUX0lOVkVSVCI6IDk5MTgxNDExNTE4OSwKICAgICJCSVRfU1RPUkUwIjogMTIzMjEyNzYyNjYzLAogICAgIkJJVF9TVE9SRTEiOiAzNDAyMjA0OTg4LAogICAgIlgiOiAxMDkyMTc1MDAwMiwKICAgICJaIjogMjM4NDk3MjEwNSwKICAgICJSIjogNDg3MzY5NDQ3NSwKICAgICJITVIiOiA3MjcxMDU0MDg5LAogICAgIkNYIjogMzE4MzI2Mjk4NTUyMywKICAgICJDWiI6IDI3NjAyMjU4MzA0LAogICAgIlNXQVAiOiAyNzI0NzMwNDU0MywKICAgICJDU1dBUCI6IDEyNTMzNzYwMDAsCiAgICAiQ0NYIjogMzcxNTg5MDI5NzUsCiAgICAiQ0NaIjogNzE0MzE5NDU1LAogICAgIlBPUF9DT05ESVRJT04iOiA3MDA5NzIwMzIwMCwKICAgICJQVVNIX0NPTkRJVElPTiI6IDcwMDk3MjAzMjAwCiAgfSwKICAibnVtX3F1Yml0cyI6IDg4OSwKICAibnVtX2JpdHMiOiAyMDgwODcsCiAgImNpcmN1aXRfc2hhMjU2IjogIjlhODJmNTQyMjY3MDcxODVmYThhN2Y1OWEyOTNlNmFmOGFiN2Q1OWJmZjA0YTRkOTI5MTllNDE3OGQ3ZDgyZjEiLAogICJ2ZXJpZmllcl9zaGEyNTYiOiAiZjE0Mjc0YmMwOTQzZmI5NzY5ZGRiMDExMzFiZTYwNjMxOTFhMTUwMDlmZTFjYWYxZDRiZGQ5ZmQyNTE5NGU2NSIsCiAgInZlcmlmaWVyX3BhdGgiOiAiL3dvcmtzcGFjZS9zY3JhdGNoLzdmNTQyZTA2YjdjZi9vZmZpY2lhbF9zb3VyY2VzL0luemFpbm9zL3ZlcmlmaWVycy9kcWkvdmVyaWZ5X3N1Ym1pc3Npb25fZHFpLnB5IiwKICAia2lja21peF9iaW5hcnlfc2hhMjU2IjogImQ5NjVlMGFkNDJlN2UzYTE0N2Q0YjI4ZDY5NzFhNTE3Zjc3MmRkNzk3OTVjZmMzNjRiZTJmZTlmZmUzYTdiODAiLAogICJraWNrbWl4X2JpbmFyeV9wYXRoIjogIi93b3Jrc3BhY2Uvc2NyYXRjaC83ZjU0MmUwNmI3Y2Yva2lja21peF92ZW52L2xpYi9weXRob24zLjEyL3NpdGUtcGFja2FnZXMva2lja21peC5jcHl0aG9uLTMxMi14ODZfNjQtbGludXgtZ251LnNvIiwKICAia2lja21peF9kaXN0cmlidXRpb25fdmVyc2lvbiI6ICIxLjAuMCIsCiAgImtpY2ttaXhfcnVudGltZV92ZXJzaW9uIjogIjAuMSIsCiAgInB5dGhvbl92ZXJzaW9uIjogIjMuMTIuMTQgKG1haW4sIEF1ZyAyNSAyMDI2LCAxNDowMDo0OSkgW0NsYW5nIDIyLjEuMyBdIiwKICAic2VlZCI6IG51bGwsCiAgInNhbHQiOiAiIiwKICAibWF4X3dvcmtlcnMiOiAxLAogICJiYXRjaF9zaXplIjogMjU2LAogICJ2ZXJpZmljYXRpb25fc2NvcGUiOiAiZnVsbCBjb21wZXRpdGlvbiB2ZXJpZmllciBkZWZhdWx0cyIsCiAgImxvYWRfc2Vjb25kcyI6IDEuNjYzMzM1OTI5OTk1ODEwMSwKICAidmVyaWZ5X3NlY29uZHMiOiAzMzQuNjQzNDI1OTc3MDAzMDYsCiAgIm1heF9yc3Nfa2liIjogNDc3OTI0NAp9Cg=='
QUALIFICATION_SHA256 = 'e98986fc57fcc920b6275f26fdd9b9db4f9f72604a24802b5a21cf85e05df714'
DONOR_ZIP_SHA256 = '1807d6ae6d2ea12b1d4bf2435f50d2513b25ade00fa0efb61390fdafb103ed37'
DONOR_ZIP_BYTES = 63552987
DQI = {'sha256': '9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1',
       'bytes': 522345615}
CHUNK = 1 << 22
NOTICE = '''# Sources and verification scope

Public portfolio: maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry,
version 3, scriptVersionId 369706978. Notebook Apache-2.0; its chemistry CC0.
The upstream page reports Public Score 27.31512 and official PASS for its
three exact pinned tasks. Those are upstream observations, not a new score
or a claim that this packaging job reran the verifiers.

https://www.kaggle.com/code/maoxin123/qcc-v27-4030-toffoli-coded-word-chemistry?scriptVersionId=369706978

Credits preserved from the upstream notebook:
- invsqrt: Syed Asad Ali generator (Apache-2.0); Ali Haydar Ozdag (ahoirg)
  64-row table; Ertugrul Ozer (ozertuu) angle refit; Asterios Panoras and
  James Barlow (manwithacat) measured-CZ/dead-write fixes. Source output:
  manwithacat's VQCC Hedge Wizardry Notebook.
- Original DQI: Syed Asad Ali v12 (Apache-2.0); ozertuu extractor cutoff;
  areebbb cutoff-18 and retained products; source ahoirg's portfolio.
- Chemistry lineage: ozertuu quantum-sim-linalg-cache (CC0), prvsiyan,
  Syed Asad Ali, Lera/marculera, Ahmed Berat Ozer, Atakan Aldemir,
  James Barlow/manwithacat dfthc_refit (Apache-2.0), busyaprime, Heliosli.
- Tasks, KickMix and verifiers: Google Quantum AI / Qualtran.

Combined DQI: corcondor/gvqcc exact4096 gauge candidate 9a82, generated
from the public DQI lineage. The unchanged official verifier ran 102400
shots before packaging: PASS, zero value and phase errors. Its full receipt
is included separately and bound to the exact DQI SHA256. A finite sampled
PASS does not prove universal absence of decoder failures.

https://github.com/corcondor/gvqcc/blob/main/score3_gauge_sort_proof.md
https://www.kaggle.com/code/geocpuresearch/gvqcc-exact4096-gauge-score2?scriptVersionId=369719696

Each circuit retains its upstream authors' terms. This packaging script is
Apache-2.0. https://www.apache.org/licenses/LICENSE-2.0
'''


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def log(event, **fields):
    print(json.dumps({'event': event, **fields}, sort_keys=True), flush=True)


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(CHUNK), b''):
            h.update(block)
    return h.hexdigest()


def verify_member(archive, name, expected):
    info = archive.getinfo(name)
    require(not info.is_dir() and not (info.flag_bits & 1), 'Invalid member: ' + name)
    require(info.file_size == expected['bytes'], 'Wrong member size: ' + name)
    h = hashlib.sha256()
    crc = count = 0
    with archive.open(info) as f:
        for block in iter(lambda: f.read(CHUNK), b''):
            h.update(block)
            crc = binascii.crc32(block, crc)
            count += len(block)
    require(count == expected['bytes'], 'Truncated member: ' + name)
    require(h.hexdigest() == expected['sha256'], 'Wrong member SHA256: ' + name)
    require((crc & 0xffffffff) == info.CRC, 'Wrong member CRC: ' + name)
    return {'sha256': h.hexdigest(), 'bytes': count, 'crc32': '%08x' % (crc & 0xffffffff)}


def verify_archive(path, members):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), 'Duplicate archive member')
        require(len(names) == 18 and set(names) == set(members), 'Expected exact 18-member portfolio')
        return {name: verify_member(z, name, spec) for name, spec in sorted(members.items())}


def zip_paths(root):
    seen = set()
    for directory, dirs, files in os.walk(root, followlinks=True):
        real = os.path.realpath(directory)
        if real in seen:
            dirs[:] = []
            continue
        seen.add(real)
        dirs.sort()
        for name in sorted(files):
            if name.lower().endswith('.zip'):
                yield Path(directory) / name


def find_inputs(root):
    public = donor = None
    rejected = []
    for p in zip_paths(root):
        if donor is None and p.stat().st_size == DONOR_ZIP_BYTES and digest(p) == DONOR_ZIP_SHA256:
            donor = p
        if public is None:
            try:
                with zipfile.ZipFile(p) as z:
                    names = z.namelist()
                    if len(names) != 18 or set(names) != set(PUBLIC['members']):
                        continue
                    if any(z.getinfo(n).file_size != s['bytes'] for n, s in PUBLIC['members'].items()):
                        continue
                verify_archive(p, PUBLIC['members'])
                public = p
            except (RuntimeError, zipfile.BadZipFile, KeyError) as exc:
                rejected.append({'path': str(p), 'reason': str(exc)})
        if public is not None and donor is not None:
            break
    require(public is not None, 'Exact v27 output ZIP not found; attach v3 output. Rejections: ' + json.dumps(rejected))
    require(donor is not None, 'Exact 1807d6ae donor ZIP not found; attach exact4096 gauge score2 v1 output')
    with zipfile.ZipFile(donor) as z:
        require(z.namelist().count('dqi.kmb') == 1, 'Missing or duplicate donor DQI')
        verify_member(z, 'dqi.kmb', DQI)
    return public, donor


def package(public, donor, target):
    expected = {name: dict(spec) for name, spec in PUBLIC['members'].items()}
    expected['dqi.kmb'] = dict(DQI)
    with zipfile.ZipFile(public) as base, zipfile.ZipFile(donor) as change:
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
            for name in sorted(expected):
                source = change if name == 'dqi.kmb' else base
                zi = zipfile.ZipInfo(name, (2026, 11, 15, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.create_system = 3
                zi.external_attr = 0o100644 << 16
                with source.open(name) as f, out.open(zi, 'w', force_zip64=True) as g:
                    shutil.copyfileobj(f, g, CHUNK)
    return verify_archive(target, expected)


def main(input_root=None, output_root=None):
    started = time.monotonic()
    root = Path(input_root or os.environ.get('QCC_INPUT', '/kaggle/input'))
    output = Path(output_root or os.environ.get('QCC_WORKING', '/kaggle/working'))
    qualification_bytes = base64.b64decode(QUALIFICATION_B64, validate=True)
    require(hashlib.sha256(qualification_bytes).hexdigest() == QUALIFICATION_SHA256, 'Qualification bytes changed')
    qualification = json.loads(qualification_bytes)
    require(qualification['status'] == 'PASS' and qualification['verified_shots'] == 102400,
            'Wrong qualification status or shot count')
    require(qualification['value_errors'] == 0 and qualification['phase_errors'] == 0,
            'Qualification contains errors')
    require(qualification['circuit_sha256'] == DQI['sha256'], 'Qualification covers different DQI')
    public, donor = find_inputs(root)
    public_sha = digest(public)
    log('inputs_verified', public_zip_sha256=public_sha, donor_zip_sha256=DONOR_ZIP_SHA256,
        public_members=18, qualification_sha256=QUALIFICATION_SHA256)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='v27-gauge-package-') as temp:
        staged = Path(temp) / 'submission.zip'
        members = package(public, donor, staged)
        changed = [name for name in members if members[name]['sha256'] != PUBLIC['members'][name]['sha256']]
        require(changed == ['dqi.kmb'], 'Unexpected changed member list: ' + repr(changed))
        combined_sha = digest(staged)
        combined_bytes = staged.stat().st_size
        receipt = {
            'status': 'EXACT_HASH_QUALIFIED_PORTFOLIO_PACKAGED',
            'submission_performed': False, 'observed_own_public_score': None,
            'upstream': PUBLIC, 'source_public_zip_sha256': public_sha,
            'source_public_zip_bytes': public.stat().st_size,
            'source_donor_zip_sha256': DONOR_ZIP_SHA256,
            'qualification_sha256': QUALIFICATION_SHA256,
            'qualification': qualification, 'changed_members': changed,
            'preserved_members': 17, 'members': members,
            'submission_zip_sha256': combined_sha, 'submission_zip_bytes': combined_bytes,
            'baseline_output': 'submission_public_v27.zip', 'combined_output': 'submission.zip',
            'validation_scope': 'Per-member SHA256, exact 18-member set, sizes and CRC. Full scientific verification is not rerun in this packaging job. DQI uses the embedded prior receipt; other 17 members match the public v27 verified portfolio byte-for-byte.',
            'seconds': time.monotonic() - started,
        }
        shutil.copyfile(public, output / 'submission_public_v27.zip')
        shutil.copyfile(staged, output / 'submission.zip')
        require(digest(output / 'submission_public_v27.zip') == public_sha, 'Baseline copy mismatch')
        require(digest(output / 'submission.zip') == combined_sha, 'Combined copy mismatch')
        (output / 'outcome_v27_combine_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        (output / 'score3_full_20261115_verification.json').write_bytes(qualification_bytes)
        (output / 'SOURCES_AND_LICENSES.md').write_text(NOTICE)
        log('ready', combined_zip_sha256=combined_sha, combined_bytes=combined_bytes,
            baseline_zip_sha256=public_sha, changed_members=changed,
            seconds=time.monotonic() - started)


if __name__ == '__main__':
    main()
