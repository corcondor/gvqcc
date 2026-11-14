#!/usr/bin/env python3
"""Build real changed KMBs and check exact phase on every legal x.
Uses integer arithmetic for phase rounding and the official isqrt oracle. This is
full-domain functional verification plus random-outcome native spot checks, not
an assertion that the official 64-shots-per-x evaluation has been rerun.
"""
import argparse,json,pathlib,subprocess,hashlib,importlib.util,sys,time,math
from fractions import Fraction
from decimal import Decimal,localcontext
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent.parent;WORK=ROOT/'invsqrt_structural_work';MAX=3133452

def dec(n):
 with localcontext() as c:
  c.prec=120;return format(Decimal(n)/Decimal(1<<80),'f')
def main():
 p=argparse.ArgumentParser();p.add_argument('--native',action='store_true');a=p.parse_args()
 if a.native:return native()
 start=time.time();desc=json.loads((WORK/'basis.json').read_text())['basis'];idx=[i for i,d in enumerate(desc) if d['kind']=='rotation' and d['class']=='rotation'];lines=(ROOT/'gvqcc_repo/invsqrt_structural_e46.kmx').read_text().splitlines()
 initial=json.loads((WORK/'results.json').read_text())['experiments'][0]
 replacements=json.loads((WORK/'replace_results.json').read_text())['experiments'];valid=[x for x in replacements if len(x['drop'])==2 and x['result'] and x['result']['margin_scaled']>0];best=min(valid,key=lambda x:x['rotation_toffoli_equiv']) if valid else None
 chosen=[('walsh34',initial)]+([('walsh32',best)] if best else [])
 plans=[]
 for name,r in chosen:
  candidate=r['candidate'];result=r['result'];drop=set(r.get('drop',r.get('drop_rotation_indices',[])));adjust=result['coeff_scaled'];coeffs={i:round(Fraction(d['half_turns'])*(1<<80)) for i,d in enumerate(desc) if d['kind']=='rotation'}
  for j,i in enumerate(idx):coeffs[i]=0 if j in drop else round((Fraction(desc[i]['half_turns'])+Fraction(float(adjust[j]*1e-11))*2)*(1<<80))
  extra=round(Fraction(float(adjust[-1]*1e-11))*2*(1<<80));byline={desc[i]['line']:(i,v) for i,v in coeffs.items()};out=[]
  for lineno,l in enumerate(lines,1):
   if lineno==candidate['line']:
    qs=candidate['qubits'];target=qs[-1]
    if len(qs)==2:out.append(f'CX q{qs[0]} q{target}')
    out.append(f'Z_POW q{target} {dec(extra)}')
    if len(qs)==2:out.append(f'CX q{qs[0]} q{target}')
   if lineno in byline:
    i,v=byline[lineno]
    if v:out.append(f'Z_POW q{desc[i]["qubit"]} {dec(v)}')
   else:out.append(l)
  kmx=ROOT/f'gvqcc_repo/invsqrt_structural_{name}.kmx';kmx.write_text('\n'.join(out)+'\n')
  plan={'name':name,'candidate':candidate,'dropped_generic_rotation_indices':sorted(drop),'kmx':str(kmx),'original_rotation_coefficients_halfturn_units2m80':{str(i):str(v) for i,v in coeffs.items()},'extra_halfturn_units2m80':str(extra),'generic_rotations':34-len(drop),'lp_result':result};plans.append(plan)
 # Baseline exact phase is included to audit the evaluator on random native branches.
 baseline={i:round(Fraction(d['half_turns'])*(1<<80)) for i,d in enumerate(desc) if d['kind']=='rotation'}
 allplans=[{'name':'baseline','original_rotation_coefficients_halfturn_units2m80':{str(i):str(v) for i,v in baseline.items()},'extra_halfturn_units2m80':'0','candidate':{'basis_indices':[0]}}]+plans
 cpp=r'''#include <fstream>
#include <vector>
#include <cstdint>
#include <string>
#include <iostream>
using U=uint64_t;using I=__int128_t;I parse(std::string s){bool neg=s[0]=='-';I v=0;for(int i=neg;i<(int)s.size();i++)v=v*10+s[i]-'0';return neg?-v:v;}
int main(int argc,char**argv){std::string dir=argv[1],name=argv[2];int nb=177,n=3133452,nw=(n+63)/64;std::vector<U>b((size_t)nb*nw);std::ifstream f(dir+"/basis.u64",std::ios::binary);f.read((char*)b.data(),b.size()*8);std::ifstream c(dir+"/"+name+"_coeff.txt");int k;std::string s;std::vector<int>is;std::vector<I>cs;while(c>>k>>s){is.push_back(k);cs.push_back(parse(s));}std::ifstream extra(dir+"/"+name+"_extra.txt");int a,z;extra>>a>>z>>s;I v=parse(s);std::vector<U>out(n);for(int x=0;x<n;x++){int w=x/64,l=x%64;I sum=0;for(int j=0;j<(int)is.size();j++)if((b[(size_t)is[j]*nw+w]>>l)&1)sum+=cs[j];if(((b[(size_t)a*nw+w]^b[(size_t)z*nw+w])>>l)&1)sum+=v;out[x]=(U)((sum+((I)1<<16))>>17);}std::ofstream o(dir+"/"+name+"_phase.u64",std::ios::binary);o.write((char*)out.data(),n*8);}
'''
 (WORK/'phase_exact.cpp').write_text(cpp);subprocess.run(['g++','-O3',str(WORK/'phase_exact.cpp'),'-o',str(WORK/'phase_exact')],check=True)
 for plan in allplans:
  coeff=plan['original_rotation_coefficients_halfturn_units2m80'].copy();coeff[str(len(desc)-1)]=str(1<<80)
  (WORK/(plan['name']+'_coeff.txt')).write_text('\n'.join(f'{k} {v}' for k,v in coeff.items()))
  bi=plan['candidate']['basis_indices'];aa,zz=(bi[0],bi[1]) if len(bi)==2 else (bi[0],45) # snapshot q41 may not zero! single case handled explicitly below
  if len(bi)==1:
   # Create a zero column by finding a documented bit function zero for whole domain.
   packed=np.memmap(WORK/'basis.u64',dtype='<u8',mode='r',shape=(len(desc),(MAX+63)//64));zz=next(j for j in range(len(desc)) if not packed[j].any());aa=bi[0]
  (WORK/(plan['name']+'_extra.txt')).write_text(f'{aa} {zz} {plan["extra_halfturn_units2m80"]}')
  subprocess.run([str(WORK/'phase_exact'),str(WORK),plan['name']],check=True)
 # Exact oracle identical to official reference_values, avoiding any sqrt/f64 approximation.
 rs=[math.isqrt((1<<130)//x) for x in range(1,MAX+1)];target=np.array([((r+1)>>1)&((1<<64)-1) for r in rs],dtype=np.uint64);tol=np.array([r>>25 for r in rs],dtype=np.uint64);del rs
 records=[]
 for plan in allplans:
  theta=np.fromfile(WORK/(plan['name']+'_phase.u64'),dtype='<u8');error=(theta-target).view(np.int64);used=abs(error).view(np.uint64);bad=int(np.count_nonzero(used>tol));m=int((tol-used).min()) if not bad else None
  record={'name':plan['name'],'phase_error_count':bad,'max_x':MAX,'min_margin_units2m64':m,'min_margin_turns':None if m is None else m/2**64,'worst_ratio':float(np.max(used/tol)),'worst_x':int(np.argmax(used/tol))+1}
  if plan['name']!='baseline' and m:
   n=plan['generic_rotations'];eps=math.pi*m/2**64/n;rotcost=n*(.56*math.log2(1/eps)+5.3)/4;record.update(generic_rotations=n,rotation_eps=eps,rotation_toffoli_equiv=rotcost,arithmetic_toffoli_from_upstream=1479.7500405453395,t_base=1,predicted_toffoli_equiv=1479.7500405453395+.25+rotcost,predicted_score=46*(1479.7500405453395+.25+rotcost))
  records.append(record);print(json.dumps(record),flush=True)
 (WORK/'build_plans.json').write_text(json.dumps(plans,indent=2));(ROOT/'gvqcc_repo/invsqrt_structural_domain.json').write_text(json.dumps({'contract':'all x=1..3133452; official integer oracle; circuit phase evaluated with exact integer sums, round-to-nearest 2^-64 turns','records':records,'official_64_shots_per_x_rerun':False,'elapsed_seconds':time.time()-start},indent=2))
 subprocess.run([str(ROOT/'kickmix_venv/bin/python'),__file__,'--native'],check=True)

def native():
 import kickmix as km
 spec=importlib.util.spec_from_file_location('invsqrt_official',ROOT/'official_sources/Inzainos/verifiers/invsqrt/verify_submission_invsqrt.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
 plans=json.loads((WORK/'build_plans.json').read_text());d=json.loads((ROOT/'gvqcc_repo/invsqrt_structural_domain.json').read_text());worst=[x['worst_x'] for x in d['records']];xs=np.unique(np.r_[np.arange(1,2049),np.linspace(1,MAX,2048,dtype=int),worst]).astype(np.uint64);xs=np.resize(xs,((len(xs)+255)//256)*256);results=[]
 allplans=[{'name':'baseline','path':ROOT/'dqi_inputs/invsqrt_e46d90c36d1b.kmb'}]+plans
 for plan in allplans:
  c=km.Circuit.from_file(str(plan.get('kmx',plan.get('path'))));name=plan['name'];expected=np.memmap(WORK/(name+'_phase.u64'),dtype='<u8',mode='r');xr,scratch=m.validate_registers(c,m.ProblemSpecInvSqrt.for_n_p(10));fail=0;phasebad=0;cases=0;tot=0
  for seed in (20261116,20261117,20261118):
   sim=km.Simulator(batch_size=256,debug_print=False,counting_operations=True,seed=seed)
   for st in range(0,len(xs),256):
    xx=xs[st:st+256];sim.clear_for_shot();sim.write_across_shots(xr,m.to_bits(xx,22));sim.do(c);fail+=int(np.count_nonzero(m.from_bits(sim.read_across_shots(xr))!=xx));fail+=int(np.any(sim.read_across_shots(scratch),axis=0).sum());theta=np.array([m.half_turns_to_units(sim.read_shot_phase(i)) for i in range(256)],dtype=np.uint64);phasebad+=int(np.count_nonzero(theta!=expected[xx-1]));cases+=256
   tot+=int(sim.operation_statistics().num_toffoli_like)
  static=c.operation_statistics()
  result={'static_generic_rotations':int(static.num_z_pow(min_clifford_hierarchy_level=4)),'static_t_class':int(static.num_t_like),'static_toffoli':int(static.num_toffoli_like),'name':name,'native_cases':cases,'random_seeds':[20261116,20261117,20261118],'restoration_failures':fail,'exact_phase_mismatches':phasebad,'qubits':c.num_qubits,'ops':len(c),'sample_total_toffoli':tot,'sample_mean_toffoli':tot/cases}
  if name!='baseline':
   out=ROOT/f'gvqcc_repo/invsqrt_structural_{name}.kmb';c.to_file(str(out),format='kmb');result.update(kmb=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),bytes=out.stat().st_size)
  print(json.dumps(result),flush=True);results.append(result)
  if fail or phasebad:raise RuntimeError('native check failed')
 (ROOT/'gvqcc_repo/invsqrt_structural_native.json').write_text(json.dumps({'records':results,'meaning':'Native random HMR outcomes at deterministic x set; complements exact full-domain phase and structural input-dependent diagonal proof, not full official 200M-shot run.'},indent=2))
if __name__=='__main__':main()
