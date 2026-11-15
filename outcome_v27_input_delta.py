#!/usr/bin/env python3
"""Read pinned publicv27 and previously submitted local factorization in Kaggle.

CPU/numpy, no network or credentials. Produces an exact reproducible angleword
delta for subsequent synthesis; it neither edits inputs nor submits a circuit.
Publicv27 chemistry is CC0; source maoxin123, notebook369706978.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile
import zlib
import numpy as np

PINS = {
    'public_v27': '4df35abdeec320a3f1c10f6f533e73550e50bb45d95e666deaa01062810a3559',
    'local_score2': '5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357',
}
found = {}
seen = set()
for folder, dirs, files in os.walk('/kaggle/input', followlinks=True):
    real = os.path.realpath(folder)
    if real in seen:
        dirs[:] = []
        continue
    seen.add(real)
    for name in sorted(files):
        p = Path(folder) / name
        if p.suffix.lower() != '.zip':
            continue
        try:
            with zipfile.ZipFile(p) as archive:
                if 'dfthcsos/submission.npz' not in archive.namelist():
                    continue
                blob = archive.read('dfthcsos/submission.npz')
        except (zipfile.BadZipFile, KeyError):
            continue
        digest = hashlib.sha256(blob).hexdigest()
        for label, pinned in PINS.items():
            if digest == pinned and label not in found:
                with np.load(io.BytesIO(blob), allow_pickle=False) as data:
                    found[label] = {key: data[key].copy() for key in data.files}
                print(json.dumps({'event':'input_found','label':label,'npz_sha256':digest,'path':str(p)}), flush=True)
    if len(found) == 2:
        break
assert set(found) == set(PINS), 'Attach publicv27 and exact4096gauge score2 notebookoutputs'
old, new = found['local_score2'], found['public_v27']
a = np.asarray(old['angle_words'], dtype=np.uint8)
b = np.asarray(new['angle_words'], dtype=np.uint8)
assert a.shape == b.shape == (1220, 75)
indices = np.argwhere(a != b)
receipt = {
    'status': 'EXACT_PINNED_PUBLIC_INPUT_COMPARISON',
    'source_npz_sha256': PINS,
    'public_angle_shape': list(b.shape),
    'public_uint8_words_sha256': hashlib.sha256(b.tobytes()).hexdigest(),
    'old_uint8_words_sha256': hashlib.sha256(a.tobytes()).hexdigest(),
    'changed_words': len(indices),
    'arrays': {key: {'old_shape':list(old[key].shape),'new_shape':list(new[key].shape),
                     'equal':bool(np.array_equal(old[key],new[key])),
                     'new_raw_sha256':hashlib.sha256(new[key].tobytes()).hexdigest()}
               for key in new if key in old},
}
out = Path('/kaggle/working')
np.save(out/'public_v27_angle_words_uint8.npy',b,allow_pickle=False)
if len(indices) <= 4096:
    receipt['angle_word_changes'] = [[int(i),int(j),int(a[i,j]),int(b[i,j])] for i,j in indices]
else:
    receipt['public_words_zlib_base64'] = base64.b64encode(zlib.compress(b.tobytes(),9)).decode()
(out/'outcome_v27_input_delta.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('INPUT_DELTA_BEGIN', flush=True)
print(json.dumps(receipt,separators=(',',':')), flush=True)
print('INPUT_DELTA_END', flush=True)
