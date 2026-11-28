import os,sys,pathlib,types,json,hashlib,gc,importlib
import kickmix as km
from transport42_lean import gate_tape
from apply_coefficient_fusion import rewrite
import cf_route
base=pathlib.Path('/tmp/fusion/third_party/thembones-milestone-generators-v2/dqi');kit=base/'kit/kv_unfused5';tools=base/'tools'
sys.modules['circ']=km
sys.path[:0]=[str(tools),str(kit),str(kit/'exp/new/root'),str(kit/'exp/new/a01'),str(kit/'exp/round7/root'),str(kit/'exp/next/carry')]
os.environ.update(DQI_KIT=str(kit),DQI_BUILD_SOURCE=str(kit),Z2_PDR_BLOCKS='15,13,11',Z2_PDR_RBLOCKS='15,13,11',Z2_PDR_REV='1',Z2_PDR_LOCAL='1',Z2_PDR_SHARE='1',Z2_PDR_LIVEB='1',PDRFIX_BC='1',PDRFIX_ROUTE='1',DQI_INT_MON1_MERGE='1',DQI_INT_MON1_OUT='/tmp/fusion/patch/mon1.json',DQI_INT_MHR_E='1',DQI_INT_MHR_XOFF='1',DQI_INT_MHR_LEVELS='11,13',DQI_INT_MHR_EARLYF='1',DQI_INT_MHR_EARLY_LEVELS='11,13',DQI_INT_PFDP='1')
for x in ('DQI_INT_ZC_CEIL','DQI_INT_II_CEIL','DQI_DQ3_NPAIR_CEIL','DQI_DQ3_KPN_CEIL','DQI_DQ3_W901_CEIL','DQI_DQ3_INV24_CEIL','DQI_DQ3_OM36_CEIL','DQI_INT_RC_CEIL'):os.environ[x]='899'
import loader_cache;loader_cache.install()
import walk_bound
import decode_trace_merged_completed_return as dec
decode=dec.decode;ns=types.SimpleNamespace(decode=decode)
def install(name):
 m=importlib.import_module(name)
 if hasattr(m,'_target'):
  o=m._target;m._target=lambda f,old=o:isinstance(f,types.FunctionType) and old(f)
 print(name,str(m.install(km,ns))[:500],flush=True)
install('dqi_build_patch_prefix5')
import dqi_z2_pdr as P;P.install(km,ns)
import dqi_int_pdrfix as fix
newsource=rewrite(pathlib.Path(fix.__file__).read_text())
import dqi_int_convtest
for x in ('dqi_dq3_hflag','dqi_int_zcache','dqi_int_iicache','dqi_dq3_npair','dqi_dq3_kpn','dqi_int_fdots','dqi_int_prek'):install(x)
ar=P._ar();orig=ar.mul_xor0
def mul(b,x,y,z):
 if len(x)==len(y)==len(z)==12 and len(set(map(str,list(x)+list(y)+list(z))))==36:return gate_tape(b,x,y,z)
 return orig(b,x,y,z)
exec(compile(newsource,fix.__file__+':pole33','exec'),fix.__dict__)
fix._route_rest=types.FunctionType(cf_route._route_rest.__code__,fix.__dict__)
fix.install(km,ns);ar.mul_xor0=mul
import pole33_narrow as pole
G=decode.__globals__['g'];syn=G['synthesize'];scope=syn.__globals__;folds=scope['folds']
sg,ug=dict(folds.sg),dict(folds.ug);fwd,rev=sg['absorb_even'],ug['absorb_even'];state={}
def fw(b,head,A,B,Q,r,c,kap,reverse=False,transcript=None):
 if len(B)!=1 or kap!=3104:return fwd(b,head,A,B,Q,r,c,kap,reverse,transcript)
 h=b.alloc_qubits(1)[0];state['flag']=h
 pole.guards(b,head,A[0],A[1],B[0],r,Q,h,state['pole'])
 N,D,t=fwd(b,head,A,B,Q,r,c,kap,reverse,transcript);pole.chart(b,N,D,r,Q,h);return N,D,t
def rv(b,head,A,B,Q,r,c,kap,reverse=False,transcript=None):
 if len(B)!=1 or kap!=3104:return rev(b,head,A,B,Q,r,c,kap,reverse,transcript)
 h=state.pop('flag');pole.chart(b,head+B,A,r,Q,h,True)
 out=rev(b,head,A,B,Q,r,c,kap,reverse,transcript)
 pole.guards(b,head,A[0],A[1],B[0],r,Q,h,state['pole']);b.free(h);return out
sg['absorb_even']=fw;ug['absorb_even']=rv
syn=types.FunctionType(syn.__code__,dict(scope,folds=types.SimpleNamespace(**dict(vars(folds),sg=sg,ug=ug))),syn.__name__,syn.__defaults__,syn.__closure__)
for x in ('dqi_int_pfdp','dqi_int_root4','dqi_int_mhr','dqi_int_rinvc','dqi_dq3_inv24','dqi_dq3_om36','dqi_int_mon1','r46_dqi_ext_fgret','dqi_dq3_w901'):install(x)
# Cross-word alias: fold one high coefficient into the low output and repay from q0.
# Shifted scaling: transport shared scalar through the reverse aligned levels.
os.environ.update(ZN_ALIAS_LEVELS=','.join(map(str,range(3,17))),ZN_ALIAS_B='3,4,5',DQI_INT_SS_MAXM='11')
for x in ('dqi_zn_alias','dqi_int_shiftscale'):
    install(x)
from fft_fusion import fft_scan
b=km.CircuitBuilder();b.set_max_qubits(900);S=[b.alloc_qubits(12) for _ in range(70)];E=[b.alloc_bits(12) for _ in range(4095)]
def stage(n,f):
 print('START',n,b.num_allocated_qubits,flush=True)
 with b.mark(n):v=f()
 print('DONE',n,b.num_allocated_qubits,flush=True);return v
mt=stage('mask_projection',lambda:G['baseline'].project(b,S,E))
stage('initial',lambda:G['linear_words'](b,S,G['matrix']))
et=stage('extract',lambda:G['extraction'](b,S));state['pole']=et['pole']
A,B,undo=stage('synthesis',lambda:syn(b,S,et['pole']))
ct=stage('half_degree_convert',lambda:G['convert_safe'](b,A,B,monic_root=True))

def ids(X):return [[int(str(y).lstrip('q')) for y in x] for x in X]
print('A_B_IDS',json.dumps([ids(A),ids(B)]),flush=True)
pathlib.Path('ab_ids.json').write_text(json.dumps([ids(A),ids(B)]))
