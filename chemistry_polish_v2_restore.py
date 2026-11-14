"""Restore a full factorization from a pinned baseline and W/H2_I checkpoint.

Array identity is authoritative. ZIP byte identity is also checked but may
vary with NumPy/zlib packaging versions; the summary records both hashes.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np

def arrays_sha256(data):
 h=hashlib.sha256()
 for key in sorted(data):
  raw=np.asarray(data[key]);a=np.ascontiguousarray(raw);header=json.dumps({'key':key,'dtype':raw.dtype.str,'shape':list(raw.shape)},sort_keys=True,separators=(',',':')).encode()
  h.update(len(header).to_bytes(8,'big'));h.update(header);h.update(a.tobytes(order='C'))
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--base',type=Path,required=True);p.add_argument('--weights',type=Path,required=True);p.add_argument('--summary',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();summary=json.loads(a.summary.read_text())
 expected_base=summary['baseline']['sha256'];actual_base=hashlib.sha256(a.base.read_bytes()).hexdigest()
 if actual_base!=expected_base:raise ValueError(f'Baseline SHA256 mismatch: expected {expected_base}, got {actual_base}')
 weight_sha=hashlib.sha256(a.weights.read_bytes()).hexdigest()
 entries=[r for r in summary['selected'] if r['weights_checkpoint']['sha256']==weight_sha]
 if len(entries)!=1:raise ValueError('Checkpoint SHA256 does not identify one selected candidate in the summary')
 entry=entries[0];data=dict(np.load(a.base));weights=dict(np.load(a.weights))
 if set(weights)!={'W','H2_I'}:raise ValueError('Checkpoint must contain exactly W and H2_I')
 data.update(weights)
 arrays_sha=arrays_sha256(data)
 if arrays_sha!=entry['canonical_arrays_sha256']:raise ValueError('Restored arrays differ from the recorded full candidate')
 a.out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(a.out,**data)
 actual_full=hashlib.sha256(a.out.read_bytes()).hexdigest()
 print(json.dumps({'output':str(a.out),'arrays_verified':True,'canonical_arrays_sha256':arrays_sha,'full_candidate_sha256':actual_full,'byte_identical_to_recorded_candidate':actual_full==entry['sha256'],'numpy_version':np.__version__},indent=2))

if __name__=='__main__':main()
