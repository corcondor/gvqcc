"""KickMix native diagnostic gate: ONE fixed KMB, fail-closed. Not official.

Requires pinned KickMix and verify_submission_dqi in PYTHONPATH, and the
phase_probe.py already present in PR #227. Does not silently skip unavailable
KickMix inputs. This panel alone is NOT whole-oracle correctness.
"""
import argparse, json, pathlib, subprocess, sys

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("candidate",type=pathlib.Path)
    ap.add_argument("--probe",required=True,type=pathlib.Path)
    ap.add_argument("--receipt",required=True,type=pathlib.Path)
    p=ap.parse_args()
    if not p.candidate.is_file() or not p.probe.is_file():
        ap.error("native KMB or PR#227 KickMix probe unavailable")
    p.receipt.parent.mkdir(parents=True,exist_ok=True)
    r=subprocess.run([sys.executable,str(p.probe),str(p.candidate),
                      str(p.receipt)],check=False)
    if r.returncode or not p.receipt.exists():
        raise SystemExit("FAIL: native paired diagnostic did not run")
    z=json.loads(p.receipt.read_text())
    if z.get("num_paired_probes",0)<216:
        raise SystemExit("FAIL: insufficient native paired samples")
    hard=("zero_mask_restore_errors","onehot_restore_errors",
          "mask_restore_errors","zero_mask_dirty","onehot_dirty",
          "zero_phase_errors","mask_phase_difference_errors",
          "output_value_mask_dependence")
    for k in hard:
        if k not in z or z[k]:
            raise SystemExit("FAIL: "+k+"="+str(z.get(k,"missing")))
    print("PASS limited KickMix diagnostic; all-branch and official verifier still required")

if __name__=="__main__": main()
