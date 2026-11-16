"""Isolate and audit a reported 22,411-cost invsqrt circuit under the ORIGINAL verifier.

Not execute any third-party Python. Downloads only a pinned binary KMB, and
verifies it using a pinned, independent, unchanged official verifier.
"""
from pathlib import Path
import urllib.request,hashlib,subprocess,sys,json,os
OUT=Path(os.getenv("INVSQRT_PROBE_OUT", "/tmp/gvqcc-external-invsqrt"))
OUT.mkdir(parents=True,exist_ok=True)
repo="https://raw.githubusercontent.com/alexon-v8/quantum-circuit-compilation-invsqrt/ce4dacce473717480c40b8fb575d8904617c6b41/invsqrt.kmb"
verify="https://raw.githubusercontent.com/Inzainos/quantum-circuit-compilation/4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/invsqrt/verify_submission_invsqrt.py"
EXPECTED_VERIFIER_SHA="ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a"
def fetch(url,name,cap):
    raw=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"read-only-vqcc-audit"}),timeout=50).read(cap+1)
    if len(raw)>cap:raise ValueError("Source too large")
    dest=OUT/name;dest.write_bytes(raw)
    return {"path":str(dest),"size":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
result={"source":"alexon-v8 20-point", "official_verifier_unchanged":False,"kaggle_submit":False}
try:
    result["circuit"]=fetch(repo,"candidate.kmb",50_000_000)
    result["verifier"]=fetch(verify,"verify_submission_invsqrt.py",150_000)
    if result["verifier"]["sha256"]!=EXPECTED_VERIFIER_SHA:raise RuntimeError("Official verifier SHA mismatch; refusing test")
    result["official_verifier_unchanged"]=True
    proc=subprocess.run([sys.executable,str(OUT/"verify_submission_invsqrt.py"),
                          str(OUT/"candidate.kmb"),"--max-workers","2"],
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=700)
    result["exit_code"]=proc.returncode
    (OUT/"stdout.log").write_text(proc.stdout)
    (OUT/"stderr.log").write_text(proc.stderr)
    result["stdout_tail"]=proc.stdout[-5000:]
    result["stderr_tail"]=proc.stderr[-2500:]
    try:result["verifier_result"]=json.loads(proc.stdout)
    except Exception:pass
    result["status"]="OFFICIAL_PASS" if proc.returncode==0 and result.get("verifier_result",{}).get("status")=="PASS" else "OFFICIAL_FAIL"
except Exception as e:
    result.update(status="ERROR",error=str(e))
(OUT/"external_invsqrt_audit.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2),flush=True)
