import zipfile,hashlib,json,sys
from pathlib import Path
m=json.load(open(sys.argv[2]))
record=m['members']
expected={n:v['sha256'] if isinstance(v,dict) else v for n,v in record.items()}
p=Path(sys.argv[1])
h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
if 'archive_sha256' in m:assert h==m['archive_sha256']
with zipfile.ZipFile(p) as f:
    assert len(f.namelist())==18 and set(f.namelist())==set(expected)
    for k,v in expected.items():
        with f.open(k) as x: assert hashlib.file_digest(x,'sha256').hexdigest()==v,k
print(json.dumps({'name':p.name,'archive_sha256':h,'verified_members':18,'member_hashes':expected},indent=2))
