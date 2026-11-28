import fs from 'node:fs';
function searchF4(seed,steps,s0){
 const mul=(v,k)=>{if(!k)return 0;if(k===1)return v;let w=((v&0xaaaaaa)>>>1)^((v&0x555555)<<1)^(v&0xaaaaaa);return k===2?w:w^v};
 const sm=(a,b)=>mul(a,b)&3,iv=[0,1,3,2],at=(x,i)=>(x>>>(2*i))&3;
 function norm(a){if(!a)return [0,0];let i=(31-Math.clz32(a&-a))&~1,k=(a>>>i)&3;return [mul(a,iv[k]),k]}
 function canon(t){if(t.some(x=>!x))return null;let [a,k]=norm(t[0]),[b,l]=norm(t[1]);return [a,b,mul(t[2],sm(k,l))]}
 function align(t,p){let z=t.slice(),[x,k]=norm(z[p]);z[p]=x;z[(p+2)%3]=mul(z[(p+2)%3],k);return z}
 function sig(T){let A=new Uint32Array(144);for(let [a,b,c] of T)for(let i=0;i<12;i++)if(at(a,i))for(let j=0;j<12;j++){let v=sm(at(a,i),at(b,j));if(v)A[i*12+j]^=mul(c,v)}return A}
 let state=s0>>>0;function rnd(n){state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)%n}
 const clone=T=>T.map(x=>x.slice());
 const groups=(T,p)=>{let map=new Map();for(let i=0;i<T.length;i++){let x=norm(T[i][p])[0],v=map.get(x);if(!v){v=[];map.set(x,v)}v.push(i)}return map};
 function pool(T,p,grp){
   let rows=new Map(),B=[],C=[];const u=(p+1)%3,v=(p+2)%3;let a=norm(T[grp[0]][p])[0];
   for(let i of grp){let t=align(T[i],p),x=t[u],w=t[v];while(x){let j=(31-Math.clz32(x))>>1,b=at(x,j),old=rows.get(j);if(!old){x=mul(x,iv[b]);w=mul(w,b);rows.set(j,[x,B.length]);B.push(x);C.push(w);break}x^=mul(old[0],b);C[old[1]]^=mul(w,b)}}
   let R=[];for(let i=0;i<B.length;i++)if(C[i]){let t=[0,0,0];t[p]=a;t[u]=B[i];t[v]=C[i];R.push(canon(t))}
   if(R.length>=grp.length)return null;let S=new Set(grp);return T.filter((_,i)=>!S.has(i)).concat(R)
 }
 function reduce(T){let changed=true;while(changed){changed=false;for(let p=0;p<3;p++){let g=groups(T,p);for(let v of g.values())if(v.length>1){let z=pool(T,p,v);if(z){stats.reductions+=T.length-z.length;T=z;changed=true;break}}if(changed)break}}return T}
 const outer=(a,b)=>Array.from({length:12},(_,i)=>mul(b,at(a,i)));
 const xorM=(a,b)=>a.map((x,i)=>x^b[i]);
 function rankone(M){let i=M.findIndex(x=>x);if(i<0)return [0,0];let b=M[i],j=(31-Math.clz32(b&-b))>>1,v=at(b,j),a=0;for(let k=0;k<12;k++){let c=sm(at(M[k],j),iv[v]);if(mul(b,c)!==M[k])return null;a|=c<<(2*k)}return [a,b]}
 function span2(a,b){let m=new Set();for(let i=0;i<4;i++)for(let j=0;j<4;j++){let x=mul(a,i)^mul(b,j);if(x)m.add(norm(x)[0])}return [...m]}
 function tri(a,b,c,p,l,k){
   const u=(p+1)%3,v=(p+2)%3;
   // c[p]=l*a[p]+k*b[p] exactly. p vectors a and b independent.
   let M=xorM(outer(a[u],a[v]),outer(mul(c[u],l),c[v])),N=xorM(outer(b[u],b[v]),outer(mul(c[u],k),c[v]));
   const aa=rankone(M),bb=rankone(N),term=(x,y,z)=>{let t=[0,0,0];t[p]=x;t[u]=y;t[v]=z;return canon(t)};
   if(aa&&bb)return [term(a[p],...aa),term(b[p],...bb)].filter(Boolean);
   // All relevant planes are in the span of the three original factors.
   let L=span2(a[u],c[u]), L2=span2(b[u],c[u]), U=L.filter(x=>L2.includes(x));
   let W=span2(a[v],c[v]), W2=span2(b[v],c[v]), V=W.filter(x=>W2.includes(x));
   let options=[];
   for(let x of U)for(let y of V)for(let z=1;z<=3;z++){
     let wy=mul(y,z),X=outer(x,wy),P=rankone(xorM(M,X.map(w=>mul(w,l)))),Q=rankone(xorM(N,X.map(w=>mul(w,k))));
     if(P&&Q){
       let R=[term(a[p],...P),term(b[p],...Q),term(c[p],x,wy)].filter(Boolean);
       if(R.length<3)return R;
       if(x===norm(c[u])[0]&&outer(c[u],c[v]).every((w,i)=>w===X[i]))continue;
       options.push(R)
     }
   }
   return options.length?options[rnd(options.length)]:null
 }
 const init=seed.map(canon),want=sig(init);let T=clone(init),best=clone(init),cap=38,stats={proposals:steps,moves:0,flips:0,splits:0,tris:0,triTests:0,reductions:0,restarts:0,maxRank:33,best:33};
 for(let it=0;it<steps;it++){
  if(it%10000===9999){T=clone(best);stats.restarts++;cap=33+[2,4,6,10][rnd(4)];continue}
  let p=rnd(3),u=(p+1)%3,v=(p+2)%3,mode=rnd(100),g=groups(T,p),shared=[...g.values()].filter(a=>a.length>1),moved=false;
  if(mode<50){for(let tr=0;tr<8&&!moved;tr++){let i=rnd(T.length),j=rnd(T.length);if(i===j)continue;let a=T[i],b=T[j];if(norm(a[p])[0]===norm(b[p])[0])continue;let l=1+rnd(3),k=1+rnd(3),cp=mul(a[p],l)^mul(b[p],k),h=g.get(norm(cp)[0]);if(!h)continue;let z=h[rnd(h.length)];if(z===i||z===j)continue;let c=T[z].slice(),[_,s]=norm(c[p]),[__,t]=norm(cp);c[p]=cp;c[u]=mul(c[u],sm(s,iv[t]));stats.triTests++;let R=tri(a,b,c,p,l,k);if(R){T=T.filter((_,q)=>q!==i&&q!==j&&q!==z).concat(R);stats.tris++;moved=true}}}
  if(!moved&&mode<87&&shared.length){let h=shared[rnd(shared.length)],i=h[rnd(h.length)],j=h[rnd(h.length)];if(i!==j){let a=align(T[i],p),b=align(T[j],p),k=1+rnd(3),c=a.slice(),d=b.slice();c[u]^=mul(b[u],k);d[v]^=mul(a[v],k);T[i]=canon(c);T[j]=canon(d);T=T.filter(Boolean);stats.flips++;moved=true}}
  if(!moved&&T.length<cap){let i=rnd(T.length),j=rnd(T.length);if(i!==j){let a=T[i].slice(),b=T[j].slice(),k=1+rnd(3);b[u]=mul(b[u],k);b[v]=mul(b[v],iv[k]);let c=a.slice(),d=a.slice(),e=b.slice();c[u]^=b[u];d[p]^=b[p];d[u]=b[u];e[v]^=a[v];T=T.filter((_,id)=>id!==i&&id!==j).concat([canon(c),canon(d),canon(e)].filter(Boolean));stats.splits++;moved=true}}
  if(moved){stats.moves++;T=reduce(T);stats.maxRank=Math.max(stats.maxRank,T.length);if(T.length<best.length){best=clone(T);stats.best=best.length;if(best.length<=32)break}}
 }
 let a=sig(best),b=sig(T);if(!want.every((x,i)=>x===a[i]&&x===b[i]))throw Error("tensor mismatch");
 return {stats,best:best.length,terms:best};
}
const s=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));const out=s.map((v,i)=>searchF4(v.terms,Number(process.argv[3]||180000),0x791357+i*733));fs.writeFileSync('f4_triple_results.json',JSON.stringify(out,null,2));console.log(out.map(({terms,...r})=>r));