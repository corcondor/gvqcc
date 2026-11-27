"""Compare exact saved 622-case panel on the guarded chart and original donor.
Only 20 rows belong to the G-allpole chart. Outside it the chart oracle is identity,
so chart-contract success is not an overall DQI success.
Run PYTHONPATH=<dir of public verifier and direct_codec> python saved_panel.py fixture.npz donor.kmb chart.kmb out.json.
"""
import sys,json,pathlib,hashlib
import numpy as np,kickmix as km
import verify_submission_dqi as V
import direct_codec as D
fixture,old,new,out=map(pathlib.Path,sys.argv[1:]);z=np.load(fixture);S=z['S'].astype(np.int64);M=z['M'].astype(np.int64);phase=z['expected'].astype(bool)
G=[1]
for k in (3134,3169,3257,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054):G=D.pmul(G,[k,1,1])
hit=[]
for i,s in enumerate(S):
 t=[0]*35
 for j in range(35):
  for k,g in enumerate(G):t[j]^=D.mul(g,int(s[j+k]))
 if not any(t[:34]) and t[34]:hit.append(i)
assert hit==list(range(602,622)),hit
hit=np.array(hit);scope=np.zeros(len(S),bool);scope[hit]=True
res={'fixture_sha256':hashlib.file_digest(fixture.open('rb'),'sha256').hexdigest(),'fixture_rows':len(S),'allpole_ids':hit.tolist(),'seeds':[681,937],'errors_order':['value','mask','dirty','phase'],'results':[]}
for label,path,ids in [('donor_allpole',old,hit),('new_chart_all_622',new,np.arange(len(S)))]:
 c=km.Circuit.from_file(str(path));q,b,anc=map(km.array,V.validate_registers(c,V.ProblemSpecDQI.benchmark_instance()));eall=np.zeros(4,dtype=int);ehit=np.zeros(4,dtype=int);uall=uhit=shots=nhit=paid=0
 for seed in (681,937):
  for start in range(0,len(ids),64):
   ix=ids[start:start+64];A=V.to_bits(S[ix],12);B=V.to_bits(M[ix],12);expected=phase[ix] if label=='donor_allpole' else phase[ix]&scope[ix]
   sim=km.Simulator(batch_size=len(ix),seed=seed+start,debug_print=False,counting_operations=True);sim.use_same_registers_as(c);sim.write_across_shots(q,A);sim.write_across_shots(b,B);sim.do(c)
   errors=np.array([(sim.read_across_shots(q)!=A).any(0),(sim.read_across_shots(b)!=B).any(0),(sim.read_across_shots(anc).any(0),np.asarray(sim.read_phase_flipped_across_shots(),bool)^expected]);eall+=errors.sum(1);ehit+=errors[:,scope[ix]].sum(1);uall+=int(errors.any(0).sum());uhit+=int(errors[:,scope[ix]].any(0).sum());shots+=len(ix);nhit+=int(scope[ix].sum());paid+=int(sim.operation_statistics().num_toffoli_like)
 r=dict(label=label,sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),Q=c.num_qubits,ops=len(c),shots=shots,allpole_shots=nhit,errors=eall.tolist(),allpole_errors=ehit.tolist(),any_errors=uall,allpole_any_errors=uhit,mean_paid=paid/shots,scope='chart contract' if label.startswith('new') else 'true DQI contract on allpole rows only');res['results'].append(r);print(json.dumps(r),flush=True);del c
out.write_text(json.dumps(res,indent=2)+'\n')
