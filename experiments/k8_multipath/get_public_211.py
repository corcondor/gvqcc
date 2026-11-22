#!/usr/bin/env python3
"""Read the 33.17023 Kaggle V8 notebook as data; extract k8 without executing notebook code."""
import ast, base64, hashlib, json, lzma, os, pathlib, urllib.request
URL="https://www.kaggle.com/api/v1/kernels/pull/mizeroluckygall/quantum-circuits-33-170-3-357-toffoli-loaders"
PIN="227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898"
out=pathlib.Path("experiments/k8_multipath/artifacts");out.mkdir(parents=True,exist_ok=True)
req=urllib.request.Request(URL,headers={"User-Agent":"GVQCC-Research/1.0","Accept":"application/json"})
with urllib.request.urlopen(req,timeout=120) as response:api=json.loads(response.read(20000000))
if api["metadata"]["currentVersionNumberNullable"]!=8:raise ValueError("Version changed")
nb=json.loads(api["blob"]["sourceNullable"])
chem=None
for cell in nb["cells"]:
    code=cell["source"]
    if isinstance(code,list):code="".join(code)
    if "CHEM = {'kmb':" not in code:continue
    for stmt in ast.parse(code).body:
        if isinstance(stmt,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHEM" for t in stmt.targets):
            chem=ast.literal_eval(stmt.value)
assert chem is not None
sha,data=chem["kmb"]["dfthcsos/angle_k_8.kmb"]
raw=lzma.decompress(base64.b64decode(data))
assert sha==PIN==hashlib.sha256(raw).hexdigest()
(out/"angle_k_8_public_211T.kmb").write_bytes(raw)
import struct,collections
v,nq,nb,nr=struct.unpack_from("<4I",raw,16)
assert v==2
pos=104
for i in range(nr):
    typ,length=struct.unpack_from("<QQ",raw,pos);assert typ==0;pos+=16+length
typ,length=struct.unpack_from("<QQ",raw,pos);assert typ==1
ops=raw[pos+16:pos+16+length]
stats=collections.Counter(x&127 for x in ops)
print("V8 k8 from official public notebook:",{"sha256":sha,"bytes":len(raw),"Q":nq,"T":stats[49],"CX":stats[33],"HMR":stats[80]})
assert stats[49]==211 and nq<=128
(out/"source_receipt.json").write_text(json.dumps({"source":URL,"version":8,"sha256":sha,"num_bytes":len(raw),"Q":nq,"T":stats[49],"CX":stats[33],"HMR":stats[80]},indent=2))
