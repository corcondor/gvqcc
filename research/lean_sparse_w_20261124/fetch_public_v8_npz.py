#!/usr/bin/env python3
"""Extract SHA-pinned public V8 FeMoCo NPZ from a public Kaggle notebook as DATA.
The notebook is parsed with ast.literal_eval; NO notebook code is executed.
"""
import argparse,ast,base64,hashlib,json,lzma,urllib.request
from pathlib import Path
PIN="d4d39b2e2516ed7c51a936e863cf0567e558a0db8ded24e435f507d76bfb78d7"
URL="https://www.kaggle.com/api/v1/kernels/pull/mizeroluckygall/quantum-circuits-33-170-3-357-toffoli-loaders"

def scan(obj,label=""):
    if isinstance(obj,dict):
        print("DIAG",label,"dictionary keys",[(str(k)[:80],type(v).__name__) for k,v in list(obj.items())[:20]],flush=True)
        for key,val in obj.items():
            yield from scan(val,f"{label}/{key}")
    elif isinstance(obj,(tuple,list)):
        if len(obj)==2 and isinstance(obj[0],str) and len(obj[0])==64 and isinstance(obj[1],str):
            try:
                compressed=base64.b64decode(obj[1],validate=True)
                for fn in (lzma.decompress,lambda raw:raw):
                    try:raw=fn(compressed)
                    except Exception:continue
                    if hashlib.sha256(raw).hexdigest()==PIN:
                        print("MATCH",label,"exact SHA",PIN,"bytes",len(raw),flush=True)
                        yield raw
            except Exception as err:print("DIAG candidate",label,str(err)[:100],flush=True)
        for i,x in enumerate(obj):
            if isinstance(x,(dict,list,tuple)):
                yield from scan(x,f"{label}/{i}")

def fetch(output):
    req=urllib.request.Request(URL,headers={"User-Agent":"GVQCC-Lean-SparseW/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=140) as response:api=json.loads(response.read(35_000_000))
    print("KAGGLE_NOTEBOOK",api.get("metadata",{}).get("currentVersionNumberNullable"),flush=True)
    assert api["metadata"]["currentVersionNumberNullable"]==8
    nb=json.loads(api["blob"]["sourceNullable"])
    chem=None
    for cell in nb["cells"]:
        code=cell.get("source",[])
        if isinstance(code,list):code="".join(code)
        if "CHEM = {'kmb':" not in code:continue
        for stmt in ast.parse(code).body:
            if isinstance(stmt,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHEM" for t in stmt.targets):
                chem=ast.literal_eval(stmt.value)
    assert chem is not None,"No source CHEM literal"
    print("CHEM",list(chem.keys()),flush=True)
    for raw in scan(chem.get("weights",{}),"CHEM/weights"):
        out=Path(output);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
        print("SAVED",out,hashlib.sha256(raw).hexdigest(),flush=True)
        return
    raise ValueError("Exact NPZ not located in public CHEM weights; never substitute a different dataset")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    args=p.parse_args();fetch(args.output)
