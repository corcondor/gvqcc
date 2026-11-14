#!/usr/bin/env python3
"""General local two-zero chart repair; not a full decoder replacement.

On (N,D)!=(0,0), retain fN=[N=0],fD=[D=0], then N+=fN*D,
D+=fD*N. Both selected words are units. The two flags are needed to
reverse the map. This demo checks basis outputs and native HMR phases.
"""
from pathlib import Path
import sys,importlib.util,json,time,hashlib
import numpy as np
import kickmix as km
root=Path(__file__).resolve().parents[1]
dir=root/'official_sources/Syed_v12/source/dqi_source/src/controller_work/night_c27/controller'
sys.path.insert(0,str(dir))
import rolling_tail as Base
import rolling_tail_conditional as Conditional
start=time.monotonic()
b=km.CircuitBuilder()
n=b.create_quantum_register(24,'N');d=b.create_quantum_register(24,'D')
f=b.create_quantum_register(2,'flags')
Base.zero_xor(b,n,f[0]);Base.zero_xor(b,d,f[1])
for i in range(24):b.ccx(f[0],d[i],n[i])
for i in range(24):b.ccx(f[1],n[i],d[i])
prefix=b.finish_circuit()
for i in range(24):b.ccx(f[1],n[i],d[i])
for i in range(24):b.ccx(f[0],d[i],n[i])
Conditional.erase_zero_flag(b,n,f[0]);Conditional.erase_zero_flag(b,d,f[1])
closed=b.finish_circuit()
def bits(v,width=24):return (np.asarray(v,dtype=np.uint32)[None,:]>>np.arange(width,dtype=np.uint32)[:,None]&1).astype(bool)
rng=np.random.default_rng(88013);v=np.arange(1,4096,dtype=np.uint32)
x=np.r_[np.zeros_like(v),v,v,rng.integers(1,1<<24,2048,dtype=np.uint32),np.array([0,1103+(3094<<12)],dtype=np.uint32)]
y=np.r_[v,np.zeros_like(v),v,rng.integers(1,1<<24,2048,dtype=np.uint32),np.array([1013+(2476<<12),0],dtype=np.uint32)]
assert np.all((x!=0)|(y!=0))
fn=x==0;fd=y==0;xp=x^(fn.astype(np.uint32)*y);yp=y^(fd.astype(np.uint32)*xp)
assert np.all(xp!=0)&np.all(yp!=0)
records=[]
for seed in [31,33,104,349]:
 for label,circ,ex,ey,ef in [('prefix',prefix,xp,yp,np.array([fn,fd])),('roundtrip',closed,x,y,np.zeros((2,len(x)),dtype=bool))]:
  sim=km.Simulator(batch_size=len(x),seed=seed,counting_operations=True);sim.use_same_registers_as(circ)
  sim.write_across_shots(circ.register_data['N'],bits(x));sim.write_across_shots(circ.register_data['D'],bits(y));sim.do(circ)
  assert np.array_equal(sim.read_across_shots(circ.register_data['N']),bits(ex))
  assert np.array_equal(sim.read_across_shots(circ.register_data['D']),bits(ey))
  assert np.array_equal(sim.read_across_shots(circ.register_data['flags']),ef)
  assert not sim.read_across_shots([km.q(i) for i in range(50,circ.num_qubits)]).any()
  assert not sim.read_phase_flipped_across_shots().any()
  records.append(dict(case=label,seed=seed,shots=len(x),value_errors=0,phase_errors=0,mean_T=sim.operation_statistics().num_toffoli_like/len(x)))
result=dict(status='PASS_LOCAL_GENERAL_ZERO_CHART_COMPONENT_ONLY',domain='All(N,D) except the joint-zero pair, with clean two flag bits',algebraic_proof='If neither is zero, unchanged. If only N is zero, selected pair=(D,D),flags10. If only D is zero, selected pair=(N,N),flags01. Reverse the two controlled additions with these retained flags, then erase flags from restored source predicates. Thus all non-joint-zero inputs are covered by the case proof.',prefix_static_T=prefix.operation_statistics().num_toffoli_like,roundtrip_static_T=closed.operation_statistics().num_toffoli_like,roundtrip_expected_T=164,peak_Q_standalone=closed.num_qubits,input_data_qubits=48,persistent_chart_flags=2,additional_Q_at_later24_helper_arithmetic=2,modeled_global_Q_with864_data_and24_helpers=890,all35_slots_extra_expected_T=35*164,all35_slots_extra_static_T=35*186,naive_all35_flag_history_global_Q=864+70+24,case_count=len(x),tests=records,elapsed_seconds=time.monotonic()-start,source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(Base.__file__),Path(Conditional.__file__),Path(__file__)]},limitations=['No field multiplication, reciprocal-carry adaptation, polynomial synthesis, reverse EEA or full decoder integration.','Local phase tests sample HMR outcomes; general reversible map is proved by the3 case split using established zero-query primitives.','Existing rolling-tail flag erasure cannot be reused without a new invariant.','The additive164T/slot estimate is for this wrapper in isolation, not a proved minimum after global optimization.','The full decoder admissible domain is not extended merely by this local wrapper.'])
assert result['prefix_static_T']==94 and result['roundtrip_static_T']==186
print(json.dumps(result,indent=2))
