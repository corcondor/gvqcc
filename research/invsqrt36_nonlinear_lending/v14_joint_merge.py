import json, hashlib, sys, collections, time
from pathlib import Path
sys.path.insert(0,str(Path('p62').resolve()))
from v13_extend import full_replay, NativeKMB, des, ser, paid
from native_kmb import HEADER

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def flatten(parent, stages):
 O=NativeKMB.read(parent).ops;orig=O[:];prov=[(i,i+1,i if o.raw&127==80 else None) for i,o in enumerate(O)];changes=[];cur=sha(parent)
 for st in stages:
  st=Path(st);r=load(st/'transport.json');assert r['parent_sha256']==cur
  ed={e['range'][0]:e for e in r['selected']};out=[];np=[];i=0
  while i<len(O):
   if i not in ed:out.append(O[i]);np.append(prov[i]);i+=1;continue
   e=ed[i];a,z=e['range'];assert O[a:z]==des(e['old_gates']);g=des(e['new_gates']);l=min(p[0]for p in prov[a:z]);h=max(p[1]for p in prov[a:z]);changes.append((l,h));ev=[p[2]for p in prov[a:z]if p[2] is not None];ids=iter([ev[k]for k in e.get('event_indices',range(len(ev)))])
   assert e['new_range']==[len(out),len(out)+len(g)];out+=g;np.extend((l,h,next(ids)if o.raw&127==80 else None)for o in g);assert next(ids,None)is None;i=z
  f=st/'transport_NOT_SUBMIT.kmb';assert NativeKMB.read(f).ops==out and sha(f)==r['sha256'];cur=r['sha256'];O=out;prov=np
 spans=[]
 for a,z in sorted(changes):
  if spans and a<spans[-1][1]:spans[-1][1]=max(spans[-1][1],z)
  else:spans.append([a,z])
 out=[];j=0;prev=0
 for a,z in spans:
  j+=a-prev;start=j
  while j<len(O) and prov[j][0]<z:
   assert a<=prov[j][0] and prov[j][1]<=z;j+=1
  ev=[k for k in range(a,z)if orig[k].raw&127==80];events=[ev.index(p[2])for p in prov[start:j]if p[2] is not None]
  out.append(dict(range=[a,z],old_gates=ser(orig[a:z]),new_gates=ser(O[start:j]),event_indices=events,donor_range=[start,j],donor='61'));prev=z
 assert j+len(orig)-prev==len(O)
 return out,O,prov,r

def go(mode):
 P=Path('p61/parents/wide.kmb');K=NativeKMB.read(P);O=K.ops;assert sha(P)==sha('p62/wordwide/transport_NOT_SUBMIT.kmb')
 stages=['p61/histwide','p61/finalwide']+(['p61/defercubicwide','p61/hubwide'] if mode=='wide' else [])
 e61,o61,v61,r61=flatten(P,stages)
 r62=load('p62/v13finalwide/transport.json');e62=r62['selected'];assert r62['parent_sha256']==sha(P)
 for e in e62:e['donor']='62';e['donor_range']=e['new_range'][:]
 # Give PR62's measurement-history changes atomic priority. All PR61 edits are exact endpoint splices.
 excluded=[];selected=list(e62)
 for e in e61:
  a,z=e['range']
  if any(a<q['range'][1] and q['range'][0]<z for q in e62):excluded.append(e)
  else:selected.append(e)
 selected.sort(key=lambda e:e['range']);out=[];pos={0:0};i=0;ed={e['range'][0]:e for e in selected};maps={}
 while i<len(O):
  if i not in ed:out.append(O[i]);i+=1;pos[i]=len(out);continue
  e=ed[i];a,z=e['range'];assert O[a:z]==des(e['old_gates']);g=des(e['new_gates']);start=len(out);out+=g;e['new_range']=[start,len(out)];i=z;pos[i]=len(out);maps[(e['donor'],*e['donor_range'])]=(start,len(out))
  if e.get('old_gap_end'):pos[e['old_gap_end']]=start+e['new_gap_len']
 # For original charts, boundaries must remain aligned; for new donor charts, preserve exact range mapping.
 base=load('p61/parents/wide.json')['charts'];basekeys={tuple(c[:2])for c in base};charts=[]
 for a,z,l,h in base:
  assert l in pos and h in pos,(a,z,l,h);charts.append([a,z,pos[l],pos[h]])
 for e in e62:
  if e.get('source'):
   l,h=e['new_range'];h=l+e['new_gap_len'] if e.get('old_gap_end') else h;charts.append(e['source']+[l,h])
 for a,z,l,h in r61['charts']:
  if (a,z) in basekeys:continue
  assert l<h
  s=min(p[0]for p in v61[l:h]);t=max(p[1]for p in v61[l:h]);
  if any(s<e['range'][1] and e['range'][0]<t for e in e62):print('excluded width',a,z,s,t);continue
  assert s in pos and t in pos,(a,z,l,h,s,t);charts.append([a,z,pos[s],pos[t]])
 charts.sort();assert all(x[1]<=y[0] and x[3]<=y[2]for x,y in zip(charts,charts[1:]));assert all(q<36 for _,_,l,h in charts for o in out[l:h]for q in o.wires)
 K.ops=out;raw=K.to_bytes();header=list(HEADER.unpack_from(raw,16));header[5]=sum(len(o.wires)==3 for o in out);raw=raw[:16]+HEADER.pack(*header)+raw[16+HEADER.size:];D=Path('integrated_'+mode);D.mkdir(exist_ok=True);f=D/'transport_NOT_SUBMIT.kmb';f.write_bytes(raw);actual=NativeKMB.read(f).ops;assert actual==out
 # reconstruct serialized edits and require exact reassembly prior to running BDD
 for e in selected:e['new_gates']=ser(actual[slice(*e['new_range'])])
 r=dict(parent_sha256=sha(P),sha256=sha(f),ops=len(out),paid=paid(out),source_coverage=sum(z-a for a,z,_,_ in charts),charts=charts,selected=selected,pr61_flattened=len(e61),pr61_selected=len(e61)-len(excluded),pr62_selected=len(e62),excluded=[e['range']for e in excluded],full36=False,official_verifier=False)
 print({k:v for k,v in r.items()if k not in ('charts','selected','excluded')},flush=True)
 print('width additions', [c for c in charts if tuple(c[:2])not in basekeys],flush=True)
 (D/'transport.json').write_text(json.dumps(r,indent=2)+'\n')
 rr=full_replay(O,ed);print(rr,flush=True);r.update(rr);(D/'transport.json').write_text(json.dumps(r,indent=2)+'\n');assert rr['verification']=='PASS'
if __name__=='__main__':go(sys.argv[1])
