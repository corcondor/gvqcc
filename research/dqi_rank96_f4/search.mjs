import fs from 'node:fs';
function f4search(seed,steps,s0){
 const mul=(v,k)=>{if(!k)return 0;if(k===1)return v;let w=((v&0xaaaaaa)>>>1)^((v&0x555555)<<1)^(v&0xaaaaaa);return k===2?w:w^v};
 const sm=(a,b)=>mul(a,b)&3,iv=[0,1,3,2];
 function norm(a){if(!a)return [0,0];let i=(31-Math.clz32(a&-a))&~1,k=(a>>>i)&3;return [mul(a,iv[k]),k]}
 function canon(t){if(t.some(x=>!x))return null;let [a,k]=norm(t[0]),[b,l]=norm(t[1]);return [a,b,mul(t[2],sm(k,l))]}
 function align(t,p){let z=t.slice(),[x,k]=norm(z[p]);z[p]=x;z[(p+2)%3]=mul(z[(p+2)%3],k);return z}
 const cube=(v,j)=> (v>>>(2*j))&3;
 function sig(T){let A=new Uint32Array(144);for(let [a,b,c] of T)for(let i=0;i<12;i++){let l=cube(a,i);if(l)for(let j=0;j<12;j++){let v=sm(l,cube(b,j));if(v)A[i*12+j]^=mul(c,v)}}return A}
 let state=s0>>>0;function rnd(n){state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)%n}
 const clone=T=>T.map(x=>x.slice());
 const makeGroups=(T,p)=>{let map=new Map();for(let i=0;i<T.length;i++){let x=norm(T[i][p])[0],v=map.get(x);if(!v){v=[];map.set(x,v)}v.push(i)}return map};
 function pool(T,p,grp){
   let rows=new Map(),B=[],C=[];const u=(p+1)%3,v=(p+2)%3;let a=norm(T[grp[0]][p])[0];
   for(let i of grp){let t=align(T[i],p),x=t[u],w=t[v];while(x){let j=(31-Math.clz32(x))>>1,b=cube(x,j),old=rows.get(j);if(!old){x=mul(x,iv[b]);w=mul(w,b);rows.set(j,[x,B.length]);B.push(x);C.push(w);break}x^=mul(old[0],b);C[old[1]]^=mul(w,b)}}
   let R=[];for(let i=0;i<B.length;i++)if(C[i]){let t=[0,0,0];t[p]=a;t[u]=B[i];t[v]=C[i];R.push(canon(t))}
   if(R.length>=grp.length)return null;
   let S=new Set(grp);return T.filter((_,i)=>!S.has(i)).concat(R)
 }
 function reduce(T){let changed=true;while(changed){changed=false;for(let p=0;p<3;p++){let g=makeGroups(T,p);for(let v of g.values())if(v.length>1){let z=pool(T,p,v);if(z){stats.reductions+=T.length-z.length;T=z;changed=true;break}}if(changed)break}}return T}
 const initial=seed.map(canon),target=sig(initial);let T=clone(initial),best=clone(initial),maxRank=35,stats={proposals:steps,moves:0,flips:0,splits:0,reductions:0,restarts:0,maxRank:33,best:33};let stagnation=0;
 for(let it=0;it<steps;it++){
  if(it%5000===4999){T=clone(best);stats.restarts++;maxRank=33+[2,3,4,5,8][rnd(5)];continue}
  let mode=rnd(100),p=rnd(3),u=(p+1)%3,v=(p+2)%3;
  let groups=makeGroups(T,p),shared=[...groups.values()].filter(x=>x.length>=2),moved=false;
  if(mode<85&&shared.length){let g=shared[rnd(shared.length)],i=g[rnd(g.length)],j=g[rnd(g.length)];if(i!==j){
   let a=align(T[i],p),b=align(T[j],p),k=1+rnd(3);
   let c=a.slice(),d=b.slice();c[u]^=mul(b[u],k);d[v]^=mul(a[v],k);
   c=canon(c);d=canon(d);
   let tmp=T.slice();tmp[i]=c;tmp[j]=d;T=tmp.filter(Boolean);moved=true;stats.flips++;
  }}
  if(!moved&&T.length<maxRank){let i=rnd(T.length),j=rnd(T.length);if(i!==j){let a=T[i].slice(),b=T[j].slice(),k=1+rnd(3);
   // rescale b so its u vector is mixed with a using an arbitrary nonzero scalar
   b[u]=mul(b[u],k);b[v]=mul(b[v],iv[k]);
   let c=a.slice(),d=a.slice(),e=b.slice();
   c[u]^=b[u];d[p]^=b[p];d[u]=b[u];e[v]^=a[v];
   let z=[canon(c),canon(d),canon(e)].filter(Boolean);
   T=T.filter((_,id)=>id!==i&&id!==j).concat(z);moved=true;stats.splits++;
  }}
  if(moved){stats.moves++;T=reduce(T);stats.maxRank=Math.max(stats.maxRank,T.length);if(T.length<best.length){best=clone(T);stats.best=best.length;if(best.length<=32)break}}
 }
 let x=sig(best),y=sig(T);if(!target.every((a,i)=>a===x[i]&&a===y[i]))throw Error("tensor mismatch");
 return {stats,best:best.length,terms:best,final:T.length};
}
let seeds=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let R=seeds.map((s,i)=>f4search(s.terms,Number(process.argv[3]||200000),0x135791+i*733));fs.writeFileSync('f4_search_results.json',JSON.stringify(R,null,2));console.log(R.map(({terms,...r})=>r));
