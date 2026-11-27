M=4095;exp=[];log=[0]*4096;x=1
for i in range(M):
 exp.append(x);log[x]=i;x<<=1
 if x&4096:x^=0x1053
assert x==1;exp*=2
def mul(a,b):return exp[log[a]+log[b]] if a and b else 0
def ev(p,x):
 y=0
 for c in p[::-1]:y=mul(y,x)^c
 return y
def prod(a,b):
 r=[0]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):r[i+j]^=mul(x,y)
 return r
beta=[1,70,1971,2939,2,140,3942,1701,4,280,3743,3402];T=[0,1];S=[];tab=[]
for b in beta:
 t=ev(T,b);assert t;s=[mul(v,exp[M-log[t]]) for v in T];S.append(s)
 cols=[ev(s,1<<i) for i in range(12)];r=[0]*4096
 for i in range(1,4096):k=(i&-i).bit_length()-1;r[i]=r[i^(1<<k)]^cols[k]
 tab.append(r);tt=[0]*(2*len(T)-1)
 for i,c in enumerate(T):tt[2*i]=mul(c,c);tt[i]^=mul(t,c)
 T=tt
B=[[1]]
for i in range(1,35):j=(i&-i).bit_length()-1;B.append(prod(B[i^(1<<j)],S[j]));assert len(B[i])==i+1
with open('plan34.txt','w') as f:
 for r in [beta]+B+tab:f.write(' '.join(map(str,r))+'\n')
