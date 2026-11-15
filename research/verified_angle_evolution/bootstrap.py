"""Pin and extract the 15 ANGLE KMBs from a known 18-member Score10 ZIP.
Never changes the input archive. Unrelated private assets are never copied.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path

PINS={
0:'71735b23037e8a64d16e39b3347d440b36bdf8813613ec70c36a85bfd362d7c2',
1:'1a43bbc368785aa5fc5210f6e4d5d2f9ddf114f7f3f6d3e3964f9478056bb4be',
2:'0970b392fb4bed09d6026b77b4b31510573123cb76955030115507bffde4a6bb',
3:'f9d313326dd07028bf6ef672bb47013f01e9311695d66b8d1ee2546d7dbacd7f',
4:'0ab29f06e44ef247035c971dcca30e27616bdfdc2a102fbb58c3882bbfbfd1e0',
5:'b346df2edafbaf4d95192a974db27abf71b770f51ee61dae2eb352f422cefdf4',
6:'749d9edb817c59f8a3507400002e75c2d8db55932a6933db5c5f6f59a2679f7b',
7:'0ad7d3775a36d7c14e3d4dfa4a144267e4e9759521fae4022715be25c309638e',
8:'46e0f8d69e532438d476aa8244f257a649fdc4cffe9d41f9921758f4dc18fa83',
9:'0b995537e919351a705babb6294dfe3525ef52a3c40b08122d842f45df8182da',
10:'5fea9f297afea7ffe74054ed1b44f92031a5f6e319a7f1c8741f86c05b234834',
11:'dc425931348cc4950931c400ab19322e01495b7cf3e2d02bafabcaaf9559d28a',
12:'64bbada35a382068b8dfbca0df0d781df8704aa367882cc426b76e2767f3d13f',
13:'958789349187a70ab3baf426655aacd2360113f71ab9a7b49d6624bd0e20bcd6',
14:'f35c803dece96ceb0ba24040e7c232a73170a3692c4f5212bdeadcbfcd154212',
}

def bootstrap(zip_path:Path,target:Path):
    if target.exists() and any(target.iterdir()):raise FileExistsError('Target must be empty')
    archive=zipfile.ZipFile(zip_path)
    planned=[]
    for i in range(15):
        name=f'dfthcsos/angle_k_{i}.kmb'
        data=archive.read(name)
        sha=hashlib.sha256(data).hexdigest()
        if sha!=PINS[i]:raise ValueError(f'Unexpected baseline for batch {i}: {sha}')
        planned.append((i,data,sha))
    target.mkdir(parents=True,exist_ok=True)
    for i,data,sha in planned:(target/f'angle_k_{i}.kmb').write_bytes(data)
    return dict(status='PINNED_BASELINE_READY',sha256={str(i):s for i,_,s in planned},source_zip=str(zip_path))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('zip',type=Path);p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'inputs');args=p.parse_args()
    print(json.dumps(bootstrap(args.zip,args.out),indent=2))
