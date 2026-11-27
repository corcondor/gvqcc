"""Apply the width-only research fallbacks to a restored PR #218 kit.
Usage: python install_width_fallback.py /path/to/kv_unfused5 /path/to/build_narrow_joint.py
Put this directory on PYTHONPATH. Refuses modified anchors. Does not execute or submit.
"""
from pathlib import Path
import sys
kit=Path(sys.argv[1]);host=Path(sys.argv[2])
edits=[
    (kit/'playbook/kit/decoder/exp/safe_scalar/converter.py',
     'def scale(b,x,a,ai,divide=True):\n    out=b.alloc_qubits(12)',
     'def scale(b,x,a,ai,divide=True):\n    if b.num_allocated_qubits + 12 > b.max_qubits:\n        from native_scale import at_width\n        return at_width(b,x,a,ai,divide)\n    out=b.alloc_qubits(12)'),
    (kit.parents[1]/'tools/dqi_int_mon1.py',
     '    masks = []\n    b.x(x[0])\n',
     '    if b.num_allocated_qubits + 12 > b.max_qubits:\n        from controlled_scale import cscale_at_width\n        return cscale_at_width(b,ar,F,tops,x,y)\n    masks = []\n    b.x(x[0])\n'),
    (kit/'prior/decode_backhalf_q7.py',
     '    u = b.alloc_qubits(12)\n    for i in range(12):\n        b.init_and(F, c[i], u[i])',
     '    if b.num_allocated_qubits + 12 > b.max_qubits:\n        from masked_products import at_width\n        return at_width(b,F,payloads,c,targets,ar)\n    u = b.alloc_qubits(12)\n    for i in range(12):\n        b.init_and(F, c[i], u[i])'),
    (host,'            divide_pair_and_invert(b,[N,L],D)',
     '''            if b.num_allocated_qubits+24>b.max_qubits:
                from narrow_gauge import invert24,scale_pair
                print('LOWWIDTH reverse normalize entry',b.num_allocated_qubits,flush=True)
                invert24(b,D)
                scale_pair(b,[N,L],D)
                print('LOWWIDTH reverse normalize done',b.num_allocated_qubits,flush=True)
            else:
                divide_pair_and_invert(b,[N,L],D)''')
]
updates=[]
for p,a,z in edits:
    s=p.read_text()
    assert s.count(a)==1, p
    updates.append((p,s.replace(a,z)))
for p,s in updates:
    p.write_text(s)
    print('patched',p)
