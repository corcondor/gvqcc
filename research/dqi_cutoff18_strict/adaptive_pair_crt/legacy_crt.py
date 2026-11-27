from crt882 import *
import base64,pathlib
raw=base64.b64decode('sgf8D74BaQfBDvoC7AI2APEALQBIBaYGlAJOAnsEPQYuCqQAhwL3CxQKQA1dDvcNigS1DqQKTg82BJkCrQ85DCIDXAsvBd0LxAiAAroH8gMXCiwNzwS/AWYFGgwwBrwC9gPNC2sA+gxtCjgB8g0/AtAPYAsPBAgEMgVtD84HeQmADPEKsgebCccMKwyKChEBzwuWDZgLYAKWC8wNXwaGA/wOhAgLBTMCSwvuAiQGeQ01Bx0FBQGUBUcOVAA8AMYJRwQ0Aq4I9Q5LBbwN9QODD6UOHQz3C3kFPAxfDlMANweeBYcJGwKLAlcM2QqlApIMsQgrBIkLSwsDDI8OIAsLCcECHwx7DvwLFQEsBQAJ3wenDj0KPg+KCJ4JiwvyD8EA9wmFAQgOnQaVDM0NnQLhDy4K8gPeCrQDMwoiCbgNsgFOBrkL2QUWCEwD8wbnB00Cdw0RBpYFhwQOByQEAw+PA1IGsAMyDUcCMQ3ODxkJhAUMDu0ORwVDBgoKHQ9MDFkGLgxbCmAPCg3rDOIGjgbyDmUDDQaJCmgAKQDQC8oN5goCDBwNlwwTDjEA3wqzBWAN2ArHCAkPpA62CQgAlQYFBb0L2AIPDn0BLQCtDfUFygpOCEoGUQkCDsINCg+fCFwErwSTDwIFjgp0D30B6gRLDmkNbA38ALoPWw8WC3gIzQtsCaYBXwyJDnYDnwYSC9sGfQ5NBoICEAU6B3IPxQbvDpoCoQz5BJ0DVQJQAHcOHg8oCMYFpQ4YDmINFQ6ZAewDTA8EBNwHYg1cDn8Jwg4rDYoFGwLyA68ATQ+PAkoEnQCXDZ4AkQMxBbcJtA/WAFgJ0wnaAcIKFwSFCA4IqQyNCZgFzQkEC5wBHQL9CN8LVABDBG0NPwCqBpUBhAb/BC8CdwCDAqwGZw//C1ENvANYCXcDcgMiBhgHtAllBRACBwlMC78EsgiYDoUMqQQhABMDBAHhDcYGbwhDBlQJ1wejC/cKuwQ9DukG0gGBAlkEpAlOD9kJgge3CfUOMggLDo0JPANZDnMNpwO0CvsEQgrIALgDaQ6WALwLrwYnAPEP9AHbA00E+gG8ACcJwAi+CuYEzAW9B4oJNgqEDMINcAYZAd4AkQOrAiIAtQ4NDh4LuwYTCpIMPQsPDAALIQY1C/ELVwz9DxQNmADUBRwB3wXUDFMPkAPiB+8H9gpoCc0P4QceAYYL6g7gCZ0DbwS5Bv0PmgXRBakE2gUeATcIgg8nCZMBDQLXD00CeAN5CcoMOA0nCFkPHAE1AiULbgqmDRcL0AWODtwHbQG8AVoBZgfwBa0P+wmaDUcASwCZDGUNJg/ADMAHCwm8A1kMRApUC7UEVgTHD0sCIQliBLACqwUNAZsLVgpxC6cAJgCtCDYPvgqYB7kHagaHCPMJkQDjDnMD4wBlBOEGvguzCcsKygFRCJ8GAAILCzYBZg1RBMsBEgvBCIcF6AuQC3QKPgTNBcsEGgMyDV0NQAQJCYkN+gnPCswDsQJ/DhILAgFCCKYF4QhXDWQFOQonCzcHFAnYBqwHIwkCBBcDEw+NBXMO/gKCC88E8g/pBs8M4g3kDecPtwD7C6EGPQeACJMO/Qf4ADQBiwb1DZkJvwMUBZsAbQJsA2YPrwvjDOEFNwPRBDcO5wcvByMIZA5/C7oAsATLCD8HfQnECTILIQd+BZgJlAgmD98IXglaB/IBpAfaCXsFUQPZAggD6QsHBMwKXAp5DAsJkAOPCf8DJA7lAd4LJA4CALELTAU4A6UEGg/cAQIOSwXAAwQF1gdJABICZg8jBV4IxQ91AiAEcwrqBz0HCwXFCzEH8wGjDawC1AI2DrcJoAShAXAO4Q4UCeAC0gGkAh4PcQQjCYcDyg0FDDMA9wf+BaMEQAf8AwEL7AYPAsQEYQVKBX8OZAQUBqsMYgwzC5wJygE2DVEORQY4BQUE3A0jC5QKewIUC/gFhwIxBOMFtAkSADIGjA9uAWkDdgF/AoYLWwTkBiALww+KDZwLuw63DPMKwgWbBBkIDw1cAcMORQE4DUYI8QCPBg4AqwayDE4FWgJnD4oDOgjqBWwHrATtDqAHGASGC5YNmA+cA1ILvwkeDP8ItgPbBw0D7g5LDa4FewItDQwBkgceBvcGPQ+zBSIPDAShBzEDzALlDwUPGAHvCrUFjwRBBCULRQoHDhkAegeaAZ4E1QwyAFIMdAi/CakFgg7vBpIMTAd3BSkB6w0SDpwANAJFAXsAjwYECFQENAxnA2QKPQtMBi8NXQOYCRICvwf8AJoDiQNKAi4LqAQtBtQCkQJuCpELhggOB9kPYgj3AHMNWAPjBuQNsgbFASkGkwNSCgMMig8hCUUPTA31CEAJNALrAyIBxg26CJID+w0hB1QAkwT1B2gDOQ8dCLENqAd3ATAGjgMYAqAL7A3kCdIHvgZLBBwGmAJ4C0IBnwphDdIBqwmqC+gKcgAvBi4HVwWlDRAB2g+KCtgOzwpZBw4H0wrqAQAH9AH0CMALJwchCN0POwMcBeYH1geHAJ8DhQ/dD/EIywQ5DVcK2wULC9kJdgFOA1QPPASXCS8GzgvTDaQO7w6lCdUD1wPrArgESQD+Aw4LJQphB5cH5QMDCWYAYw+WBNoLzQeQA/oG+w5TA5cOCQs8B1UPHQUEBjEHUwO3AMYFGgZ6C0gJ4QC+D0sG+QMBAGUJlgmJDzsC4gEVD5AJygSFC3IG6gB/ACoKUg3VBiAKMQr0AGUAfQVXBw0DzwdeC8kNqga0DlQDFA9PCAIJ8Q+qBLoL1QzcARIF3Az5BbgPyAk3Bw4IoQSDCeEAFQuIAf4CfwwjCywP/AdFBfMKrQGKASoFjwAlD3YNBwgQCvkJIAXNDioKDQhoAccP4QtHDywJ0wQFAcICzQtBCPQOrA8fCcENqwfTBeMDDwcyApIHagLRDtoN5w/2BmALEQEqCiILKQyYBFQJ6QP6BZsBQQK/AuYAogXMBH4EZwXODosJRgQIALILVQVHCbsMkAnRDOwMOAlUAzwNOwPxAO4OlAt4CHkLDQ6jA0IEjw9LDkoG5QItAKsA5QvJC/0AQAbIBScDlQnSA5IG8AS/CzcIRAWZBp0O1Ar2BOwM/gJsDOUIggdMDSICsAMEC98I2QmJDSwMoAgxCJEB3wT0Bp0FUwOYD5QAJwwhBKYNAgi4DS8M+wGBC2AIAwRvAzULngb0D38J5QbcCvsHNg8jBzUNAwiTCYEHDgZYD/AEpwg2AWcEAAZOArgCoAf4AZQEKw4KCTwGWAPtBI4BWQtRDjMCpALtCssHWQ36CQIGEg6CCskMewy5DrcMzgw+DvgH0wk6BH0ElwmHD40OpwITDl8MoQ57Bo0NQQ4KCAYAdA6IBFYMYASRBCQO5gJKAgwO1Q1IDxoM8g93ClsEVgZJA4IJlAeWDukFwwzhBuIK+ASLC+0LyQxOCyUJ6wc0CcYN0gFHDDIOJwPSDXEDKAeeDDUKww+KBXgJwQCrCyQMygUCCusPlQQ4AdINOA9/CnEB9gufA1EAnQvTB4gMMQeXDqwGBAu8CrYLBAfYAMQBjwJAA8UKbwWsDEUPjAFeCrAEOAfPCeYAxQHrC+kKpgdWCp0MlgDMCVgO/A9rCP8CiAoNCwULigjfB/IBkguEAvwJ7A0lB10HcgvUAP0EFQeNDhILygeYCzQP3gZtD9UPtgfvCpkPZgGEDiwNpAqwD8wDyQnoAukHzAX+CygI3QHbBSwKzQgACQoCiQ5jBSIK1w3dBtkIdwNvCgwLOANtCNUF8AfJB3UOugzGC9oEogEoATIE/wKDBLgESAAyBdkMdQSlDRYL8wRMDWAHHQEDD6cHTAfQAxcMVwAhDTIBAAMnC3wD1AwrCHELvQ0sDHgHvwf2DZkIjQ9KDm8EywvUDRUH5wT3ABEFWgoZCQUI+gmvC8cHeg7iBuEHrA95AX4JYA1ADJgAhQUWBU4PuQN+AJ0FuABfBr8LxQRbA/4G3QCvA9QO1gm1CXMD1AGYDgEBqwEOBKwHbAh+BhcNCg/jD+kDdw6sCUgBhwBOA1YBkAutAssKtgMWDIYNdwqMCysEbQyaAvACLQ9yDwAMegiYAY8GwwtLDaUGRA+1C64KaACQB18AhQirAowA7wVeCvkF7AXsC7MEqAZAAwcOqQUQBOAGpQwEDCoCQAaNBsUMjQUdD68J2Q01B4EL7wWWDukBfgnLB5wIWQ+KCDsAiwIkBAEK9wO1AxoNaA3xA3AC+AtXBQILOQuFDdgO5Qn6C0gJwwaBB4QNFwd/DpwOnQbSBQUDfg5QB14HRQiCBngNPQZfAoMFmApQDP0DAgAjB6sMbgkMCmUKmw5EDw4BSAKwABQC4Q3hBysNRg7tC0sPRwe+A8kIPQdFAa0CJA44DbcEXgJpCI4H4wy2B4ULLQIyCGMBmwm5Ce0MRQvGC6gDUQeUA4oDcQQrDcYOCAA3C2oIYQekDqUG2AERA0sJdALgD5kKegCGB2kHvwLlBBAK')
assert hashlib.sha256(raw).hexdigest()=='a1d52d29338d0699f56f004f49d1a827903af9d62ccb2dcfa05787a2d4a086cf'
saved=np.frombuffer(raw,dtype='<u2').reshape(24,70).tolist()
def legacy_emit():
 t=Compact();work=list(range(840,882));reg=list(range(408))
 for j in range(69,-1,-1):
  for h in range(1,min(j,34)+1):
   if G[34-h]:t.constmul(word(j-h),word(j),G[34-h],12,MOD)
 conv=len(t.ops);cols=[]
 for j in range(34):
  for b in range(12):
   c=0
   for i,k in enumerate(ks):
    v=div([0]*(33-j)+[1<<b],[k,1,1])[1]
    c|=sum(x<<(12*h) for h,x in enumerate(v))<<(24*i)
   cols.append(c)
 cols=tuple(cols);base=lin_ops(cols);L=min([base]+[block_lin(cols,k) for k in range(3,10)],key=len)
 for a,b in L:t.cx(reg[a],reg[b])
 for i,k in enumerate(ks):t.inplace_inv24(reg[24*i:24*i+24],work,k)
 for a,b in reversed(L):t.cx(reg[a],reg[b])
 a,s=work[:12],work[12:24];c,h=word(68),word(69)
 start=len(t.ops);t.inv12(c,a,work[24:42]);ia=t.ops[start:].copy()
 t.lin_xor(a,word(34),[1<<i for i in range(12)])
 t.square(a,s,1,12,MOD);t.prod(h,s,word(35),12,MOD);t.constmul(a,word(35),G[33],12,MOD);t.square(a,s,1,12,MOD);t.ops.extend(reversed(ia))
 # Convert remainder plus two quotient coefficients to 36 standard polynomial coefficients in place.
 for j in range(34):
  t.constmul(word(35),word(33-j),G[j],12,MOD)
  if j:t.constmul(word(34),word(33-j),G[j-1],12,MOD)
 t.constmul(word(34),word(35),G[33],12,MOD)
 return t,conv
def words(s):
 return [xor_word(m(G[34-h],s[i-h]) for h in range(min(i,34)+1)) for i in range(70)]
def legacy_ref(s):
 w=words(s);B=trim(list(reversed(w[:34])));R=[]
 for k in ks:
  g=[k,1,1];r=div(B,g)[1];ri=inversemod(r,g) if r else []
  q,_=div(G,g)
  R=add(R,mul(q,div(mul(ri,inversemod(div(q,g)[1],g)),g)[1]))
 R=div(R,G)[1];c,h=w[68:70];a=inv(c) if c else 0
 A=w[34]^a;B=w[35]^m(h,m(a,a))^m(G[33],a)
 T=add(R,mul(G,[B,A]));T+= [0]*(36-len(T))
 return list(reversed(T[:34]))+[T[35],T[34]]+w[36:]
def recover(s):
 w=words(s);assert not any(w[34:68]) and w[68]
 o=legacy_ref(s);T=list(reversed(o[:34]))+[o[35],o[34]]
 xs=[x for x in range(1,4096) if evalp(T,x)==0];assert len(xs)==35
 dp=[T[i] if i%2 else 0 for i in range(1,36)]
 es=[inv(m(m(x,evalp(G,x)),evalp(dp,x))) for x in xs]
 assert moment(xs,es)==s
 return xs,es
def main():
 t,conv=legacy_emit();sha=hashlib.sha256(b''.join(struct.pack('<4H',*(o+(0,)*(4-len(o)))) for o in t.ops)).hexdigest()
 print('LEGACY',len(t.ops),collections.Counter(o[0] for o in t.ops),sha,flush=True)
 rng=random.Random(233234);rows=saved[:];es=[recover(s) for s in saved];assert len(es)==24
 for _ in range(128):
  xs=sorted(rng.sample(range(1,4096),35));D=[1]
  for x in xs:D=mul(D,[x,1])
  dp=[D[i] if i%2 else 0 for i in range(1,36)];c=rng.randrange(1,4096)
  ev=[m(c,inv(m(m(x,evalp(G,x)),evalp(dp,x)))) for x in xs];s=moment(xs,ev);assert recover(s)==(xs,ev);rows.append(s);es.append((xs,ev))
 for w in range(36):
  for _ in range(2):
   xs=rng.sample(range(1,4096),w);rows.append(moment(xs,[rng.randrange(1,4096) for x in xs]))
 for _ in range(128):rows.append([rng.randrange(4096) for _ in range(70)])
 expect=[legacy_ref(s) for s in rows]
 for reverse in (False,True):
  b=km.CircuitBuilder();b.set_max_qubits(882);reg=list(b.create_quantum_register(840,'data'))+list(b.alloc_qubits(42))
  for g,*a in (reversed(t.ops) if reverse else t.ops):getattr(b,('x','cx','ccx')[g])(*(reg[j] for j in a))
  b.free(km.array(reg[840:]));c=b.finish_circuit();p='/tmp/legacy_rev.kmb' if reverse else '/tmp/legacy_fwd.kmb';c.to_file(p,format='kmb');c=km.Circuit.from_file(p)
  q=km.array([km.q(i) for i in range(840)]);a=km.array([km.q(i) for i in range(840,882)]);errs=[0]*3
  inp,out=(expect,rows) if reverse else (rows,expect)
  for st in range(0,len(rows),64):
   x=np.asarray(inp[st:st+64],np.uint16);y=np.asarray(out[st:st+64],np.uint16);xb=((x[:,:,None]>>np.arange(12))&1).reshape(len(x),840).T.astype(bool);yb=((y[:,:,None]>>np.arange(12))&1).reshape(len(x),840).T.astype(bool)
   sim=km.Simulator(batch_size=len(x),seed=234+st,debug_print=False);sim.use_same_registers_as(c);sim.write_across_shots(q,xb);sim.do(c)
   e=[(sim.read_across_shots(q)!=yb).any(0),sim.read_across_shots(a).any(0),sim.read_phase_flipped_across_shots()]
   errs=[u+int(np.asarray(v).sum()) for u,v in zip(errs,e)]
  print(json.dumps(dict(reverse=reverse,Q=c.num_qubits,ops=len(c),paid=c.operation_statistics().num_toffoli_like,shots=len(rows),saved_original=24,errors=errs,kmb_sha=hashlib.file_digest(open(p,'rb'),'sha256').hexdigest())),flush=True)
  assert not any(errs)
if __name__=='__main__':main()

