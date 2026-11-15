#!/usr/bin/env python3
"""Build the complete outer/finish pair without the optional gauge-carrier data."""
from argparse import ArgumentParser
from functools import wraps
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def neutral_carrier(parent):
    class Carrier(parent):
        def park(self,unit,label=''):
            assert self.anchor is None and self.mask is None and self.b.idle and not self.b.enabled
            assert len(unit)==12
            self.anchor=unit
            self.parks+=1
            self.events.append(("park",label))

        def unpark(self,label=''):
            assert self.anchor is not None and self.mask is None and self.b.idle and not self.b.enabled
            self.anchor=None
            self.unparks+=1
            self.events.append(("unpark",label))
    return Carrier


def guarded_lender(parent, carrier_ref):
    class Lender(parent):
        def __getattr__(self,name):
            call=getattr(self.builder,name)
            if name not in ("x","z","cx","cz","ccx","ccz","swap","cswap","hmr",
                            "reset","init_and","del_and"):
                return call

            @wraps(call)
            def checked(*args,**kwargs):
                carrier=carrier_ref.get('current')
                if carrier is not None and carrier.anchor is not None:
                    anchor=set(carrier.anchor)
                    def visit(value):
                        try:
                            items=iter(value)
                        except TypeError:
                            return value in anchor
                        return any(visit(inner) for inner in items)
                    assert not any(visit(x) for x in [*args,*kwargs.values()]), name
                return call(*args,**kwargs)
            return checked
    return Lender


def build(km,pipeline,neutral,out):
    original=pipeline.Outer.GaugeCarrier
    lender=pipeline.Outer.GaugeLender
    ref={}
    if neutral:
        class Captured(neutral_carrier(original)):
            def __init__(self,*a,**k):
                super().__init__(*a,**k)
                ref['current']=self
        pipeline.Outer.GaugeCarrier=Captured
        pipeline.Outer.GaugeLender=guarded_lender(lender,ref)

    try:
        b=km.CircuitBuilder()
        b.set_max_qubits(877 if neutral else 889)
        D=[b.create_quantum_register(12,f"D{i}") for i in range(36)]
        O=[b.create_quantum_register(12,f"O{i}") for i in range(35)]
        if neutral:
            f=km.q(4096)
            mu=km.array([km.q(i) for i in range(4097,4109)])
        else:
            mu=b.create_quantum_register(12,"gauge_other")
            f=b.create_quantum_register(1,"gauge_flag")[0]
        data=km.array([q for word in D+O for q in word])
        probe=b.create_classical_register(len(data),"probe")
        abi=b.num_allocated_qubits
        phase_prefix=pipeline.Outer.emit_prefix(b,D,O,gauge_flag=f,gauge_other=mu)
        outer=b.finish_circuit()
        outer_path=out/("neutral_outer.kmb" if neutral else "baseline_outer.kmb")
        outer.to_file(outer_path,format="kmb")
        outer_stats=(outer.num_qubits,len(outer),outer.operation_statistics().num_toffoli_like)
        del outer
        finish=pipeline.Finish.emit_prefix(b,D,O)
        b.cz(probe,data)
        b.ccz(D[35][7],O[2][4],O[30][6])
        reciprocal=pipeline.Finish.emit_closing_keep_inverse(b,D,O,finish)
        pipeline.Seam.outer_closing_with_inverse(phase_prefix.lender,D,O,phase_prefix,reciprocal)
        phase_prefix.core.gauge_carrier.clean_boundary()
        assert (phase_prefix.core.gauge_carrier.parks,phase_prefix.core.gauge_carrier.unparks)==(16,16)
        assert b.num_allocated_qubits==abi
        pair=b.finish_circuit()
        pair_path=out/("neutral_pair.kmb" if neutral else "baseline_pair.kmb")
        pair.to_file(pair_path,format="kmb")
        pair_stats=(pair.num_qubits,len(pair),pair.operation_statistics().num_toffoli_like)
        return abi,(outer_path,pair_path),(outer_stats,pair_stats)
    finally:
        pipeline.Outer.GaugeCarrier=original
        pipeline.Outer.GaugeLender=lender


def matrix(w,n=12):
    return ((w[None,:]>>np.arange(n,dtype=np.uint32)[:,None])&1).astype(bool)


def simulate(km,path,neutral,abi,fixtures,seed,prefix):
    rows=len(fixtures)
    c=km.Circuit.from_file(path,format="kmb")
    sim=km.Simulator(batch_size=rows,seed=seed,counting_operations=True)
    sim.use_same_registers_as(c)
    registers=c.register_data
    expected={}
    for name,count in (("D",36),("O",35)):
        for i in range(count):
            inp=matrix(np.asarray([row[name][i] for row in fixtures],dtype=np.uint32))
            wire=f"{name}{i}"
            sim.write_across_shots(registers[wire],inp)
            if name=="O" and prefix:
                inp=matrix(np.asarray([row["expected"][i] for row in fixtures],dtype=np.uint32))
            expected[wire]=inp
    if not neutral:
        for wire,width in (("gauge_other",12),("gauge_flag",1)):
            inp=matrix(np.asarray([row[wire] for row in fixtures],dtype=np.uint32),width)
            sim.write_across_shots(registers[wire],inp)
            expected[wire]=inp
    probe=np.random.default_rng(19177632).integers(0,2,(852,rows),dtype=np.uint8).astype(bool)
    sim.write_across_shots(registers["probe"],probe)
    sim.do(c)
    for name,inp in expected.items():
        assert np.array_equal(sim.read_across_shots(registers[name]),inp),name
    assert np.array_equal(sim.read_across_shots(registers["probe"]),probe)
    assert not sim.read_across_shots(km.array([km.q(i) for i in range(abi,c.num_qubits)])).any()
    return sim.read_phase_flipped_across_shots()


def main(args):
    integ=args.source/"after_c5/integration_v3"
    release=args.source/"after_c5/release_v3/normalized"
    sys.path[:0]=list(map(str,(release,integ)))
    import integration_paths # noqa: F401
    sys.path[:0]=list(map(str,(release,integ)))
    import integrated_pipeline as pipeline
    import kickmix as km
    pipeline.configure(pipeline.Options(True,True,True,True))
    tests=args.source/"after_c5/converter_width/runs/full/fixtures.json"
    fixtures=json.loads(tests.read_text())
    assert len(fixtures)==256
    args.out.mkdir(parents=True,exist_ok=True)
    phases={}
    report=[]
    for neutral in (False,True):
        abi,paths,stats=build(km,pipeline,neutral,args.out)
        checks=[]
        for index,(path,(q,n,t)) in enumerate(zip(paths,stats)):
            for seed in (137,1137,2137):
                phase=simulate(km,path,neutral,abi,fixtures,seed,index==0)
                if index==1:
                    if neutral:
                        assert np.array_equal(phase,phases[seed])
                    else:
                        phases[seed]=phase
            checks.append(dict(path=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                               quantum=q,operations=n,static_paid=t,shots=len(fixtures)*3,
                               closed=bool(index)))
        row=dict(neutral=neutral,abi=abi,checks=checks)
        print(json.dumps(row),flush=True)
        report.append(row)
    receipt=dict(status="PASS_NATIVE_OUTER_AND_FINISH_PAIR", fixtures_sha256=hashlib.sha256(tests.read_bytes()).hexdigest(),
                 compiled_pinned_dqi=False,source_roles="gauge flag/data omitted from isolated independent outer map",
                 records=report)
    (args.out/"report.json").write_text(json.dumps(receipt,indent=2)+"\n")


if __name__=="__main__":
    cli=ArgumentParser(description=__doc__)
    for name in ("source","out"):
        cli.add_argument("--"+name,type=Path,required=True)
    main(cli.parse_args())
