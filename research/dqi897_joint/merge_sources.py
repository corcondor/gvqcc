"""Compose the two exact archived generators; this does not download assets.
Run in the archive extraction layout /mnt/data/dqi897_port:
 base/source from GVQCC_DQI_897Q_414984_Research_NOT_SUBMISSION.zip;
 donor/v127 from GVQCC_V127_898Q_410976_AdaptiveLadder_RESEARCH_NOT_SUBMISSION.zip.
The upstream kit, V124/V125 source paths, and pinned environment must be
present as in the original V127 bundle.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/dqi897_port')
out=root/'joint';out.mkdir(exist_ok=True)
p=(root/'donor/v127/build.py').read_text()
b=(root/'base/source/build_nor5.py').read_text()
sec=b[b.index('# Reverse chart without'):b.index('b=km.CircuitBuilder()')]
anchor="sys.path.insert(0,'/mnt/data/dqi_port/v127');import patch;patch.install()"
assert p.count(anchor)==1
p=p.replace(anchor,sec+"\nimport patch897;patch897.install()")
p=p.replace("out=pathlib.Path('/mnt/data/dqi_port/v127')",f"out=pathlib.Path({str(out)!r})")
(out/'build_joint.py').write_text(p)
patch=(root/'donor/v127/patch.py').read_text()
assert patch.count('898-b.num_allocated_qubits')==1
(out/'patch897.py').write_text(patch.replace('898-b.num_allocated_qubits','897-b.num_allocated_qubits'))
r=(root/'donor/v127/run.sh').read_text().replace('=898','=897').replace('WIDTH_CAP=899','WIDTH_CAP=897')
r=r.replace('$PWD/v127/mon1.json',str(out/'mon1.json')).replace('python -u v127/build.py',f'python -u {out}/build_joint.py')
(out/'run.sh').write_text(r)
print(out/'run.sh')
