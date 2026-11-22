#!/usr/bin/env python3
"""Extract the 15 public maoxin123 ANGLE KMBs from the public V8 source JSON.
Never execute notebook code. Validate every KMB with SHA256.
"""
import ast,base64,hashlib,json,lzma,pathlib,urllib.request
URL="https://www.kaggle.com/api/v1/kernels/pull/mizeroluckygall/quantum-circuits-33-170-3-357-toffoli-loaders"
OUT=pathlib.Path("experiments/k8_multipath/public_v8");OUT.mkdir(parents=True,exist_ok=True)
req=urllib.request.Request(URL,headers={"User-Agent":"GVQCC-Research/1.1","Accept":"application/json"})
with urllib.request.urlopen(req,timeout=180) as response:api=json.loads(response.read(24000000))
assert api["metadata"]["currentVersionNumberNullable"]==8
nb=json.loads(api["blob"]["sourceNullable"]);chem=None
for cell in nb["cells"]:
    code=cell["source"];code="".join(code) if isinstance(code,list) else code
    if "CHEM = {'kmb':" in code:
        for stmt in ast.parse(code).body:
            if isinstance(stmt,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHEM" for t in stmt.targets):
                chem=ast.literal_eval(stmt.value)
assert chem is not None and len(chem["kmb"])==15
assert "227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898"==chem["kmb"]["dfthcsos/angle_k_8.kmb"][0]
results=[]
import collections,struct
for i in range(15):
    name=f"dfthcsos/angle_k_{i}.kmb"
    sha,b64=chem["kmb"][name]
    raw=lzma.decompress(base64.b64decode(b64))
    assert hashlib.sha256(raw).hexdigest()==sha and raw[:16]==bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf")
    version,nq,nbit,nreg=struct.unpack_from("<4I",raw,16);assert version==2
    offset=104
    for _ in range(nreg):
        typ,size=struct.unpack_from("<QQ",raw,offset);assert typ==0;offset+=16+size
    typ,size=struct.unpack_from("<QQ",raw,offset);assert typ==1
    cnt=collections.Counter(x&127 for x in raw[offset+16:offset+16+size])
    assert nq==128 and cnt[49]>0
    (OUT/f"angle_k_{i}.kmb").write_bytes(raw)
    results.append({"i":i,"sha256":sha,"bytes":len(raw),"Q":nq,"T":cnt[49],"CX":cnt[33],"HMR":cnt[80]})
print("15 banks",sum(x["T"] for x in results))
assert sum(x["T"] for x in results)==3357
(OUT/"SHA256_BASIS.json").write_text(json.dumps({"source":URL,"version":8,"banks":results},indent=2))
