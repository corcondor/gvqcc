"""Circuit-generation worker. Evaluator must NEVER trust its cost or proof.
This isolates accidental Python state mutations, but is NOT a security sandbox.
For untrusted model code, run the worker in a network-isolated VM/container.
"""
from __future__ import annotations
import argparse,importlib.util,sys
from pathlib import Path
from kmb_v2 import load
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser();p.add_argument('program',type=Path);p.add_argument('inputs',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    originals=[load(a.inputs/f'angle_k_{i}.kmb') for i in range(15)]
    spec=importlib.util.spec_from_file_location('evolved_candidate',str(a.program.resolve()))
    if spec is None or spec.loader is None:raise ValueError('failed to import candidate')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    if not hasattr(m,'synthesize'):raise ValueError('candidate lacks synthesize(circuits)')
    out=m.synthesize(originals)
    if not isinstance(out,list) or len(out)!=15:raise TypeError('candidate must return fifteen circuits')
    a.output.mkdir(parents=True,exist_ok=False)
    for k,c in enumerate(out):c.write(a.output/f'angle_k_{k}.kmb')
if __name__=='__main__':main()
