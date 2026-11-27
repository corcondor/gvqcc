import crt882 as C
T=C.Compact();x=list(range(12));n=list(range(12,18));h=list(range(18,24));tmp=list(range(24,30))
T.frame(x,C.BASIS12,True)
a,b=x[:6],x[6:]
def norm(t):
 T.square(a,t,1,6,0x43);T.square(b,t,C.K6,6,0x43);T.prod(a,b,t,6,0x43)
norm(n);T.inv6(n,h,tmp)
for i,j in zip(b,a):T.cx(i,j)
for r in (a,b):
 T.prod(r,h,tmp,6,0x43)
 for i,j in zip(r,tmp):T.cx(i,j);T.cx(j,i);T.cx(i,j)
 T.prod(r,n,tmp,6,0x43)
T.inv6(h,n,tmp);norm(h);T.frame(x,C.BASIS12)
# Exhaustively check the local reversible template for all 4096 field words.
u=[sum(1<<v for v in range(4096) if (v>>i)&1) for i in range(12)]+[0]*18
ALL=(1<<4096)-1
for g,*q in T.ops:
 if g==0:u[q[0]]^=ALL
 elif g==1:u[q[1]]^=u[q[0]]
 else:u[q[2]]^=u[q[0]]&u[q[1]]
assert not any(u[12:])
for v in range(4096):assert sum(((u[i]>>v)&1)<<i for i in range(12))==(C.inv(v) if v else 0)
print('INV12 template',len(T.ops),sum(g[0]==2 for g in T.ops),'4096/4096 exact',flush=True)
with open('templates.hpp','w') as f:
 f.write('const int CODES[]={'+','.join(map(str,C.CODES))+'};\n')
 f.write('const int IT[][4]={'+','.join('{'+','.join(map(str,(*g,*([0]*(4-len(g))))))+'}' for g in T.ops)+'};\n')
 f.write('const int KK[]={'+','.join(map(str,C.ks))+'};\n')
