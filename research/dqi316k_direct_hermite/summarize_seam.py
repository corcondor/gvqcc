import json,itertools,collections
L=json.load(open('labels.json')); E=json.load(open('seam_inputs.json'))[128:]
def rank(x):
 d={}
 for v in x:
  while v:
   i=v.bit_length()-1
   if i not in d:d[i]=v;break
   v^=d[i]
 return len(d)
best={};first={};full=[]
for key,lines in itertools.groupby(open('donor_seams.tsv'),lambda s:s.split()[0]):
 cut=int(key); groups=collections.defaultdict(list)
 for l in lines:
  a,p,q,w,m,bad=l.split();w=int(w);t,node,kind,field=L[w];groups[t,node,kind].append((int(q),int(m)<<(12*field),int(bad,16),int(p)))
 for g,rows in groups.items():
  want=24 if g[-1]=='h' else 48
  r=rank(v[1] for v in rows)
  b=0
  for _,_,v,_ in rows:b|=v
  if r and (g not in best or r>best[g][0]):
   best[g]=(r,cut,rows[0][3],len(rows),b)
  if r>=want:
   if g not in first:first[g]=(cut,rows[0][3],b,len(rows))
   if b and g not in [x[0] for x in full]:full.append((g,cut,rows[0][3],b,len(rows)))
for g in sorted(best):
 if g[-1]=='h' or g[0] in (6,8,10):
  z=best[g];print(g,z[:4], 'bad weights',sorted(set(len(E[i]) for i in range(64) if z[4]>>i&1)))
print('FIRST FULL BAD',[(g,c,p,sorted(set(len(E[i])for i in range(64)if b>>i&1)),n)for g,c,p,b,n in sorted(full,key=lambda x:x[1])][:30])
json.dump(dict(best=[(g,z)for g,z in best.items()],first=[(g,z)for g,z in first.items()],full=full),open('seams_summary.json','w'))
