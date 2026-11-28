import fs from 'node:fs';
function mixedF4(seed,steps,s0){
 const L=((1n<<48n)-1n)/3n,H=L<<1n,L24=0x555555,H24=0xaaaaaa,iv=[0,1,3,2];
 const sm=(a,b)=>{let w=((a&2)>>1)^((a&1)<<1)^(a&2);return b===0?0:b===1?a:b===2?w:w^a};
 const scale=(x,k)=>{if(k===0)return 0n;if(k===1)return x;let w=((x&H)>>1n)^((x&L)<<1n)^(x&H);return k===2?w:w^x};
 const sc=(x,k)=>{if(k===0)return 0;if(k===1)return x;let w=((x&H24)>>>1)^((x&L24)<<1)^(x&H24);return k===2?w:w^x};
 const pos=Array.from({length:24},(_,i)=>BigInt(2*i)), at=(x,i)=>Number(x>>pos[i]&3n);
 const first=x=>((x&-x).toString(2).length-1)>>1;
 const norm=x=>x?scale(x,iv[at(x,first(x))]):0n;
 const ow=x=>{if(!x)return [0,0];let i=(31-Math.clz32(x&-x))>>1,k=(x>>>(2*i))&3;return [sc(x,iv[k]),k]};
 function canon(a,b,w){if(!a||!b||!w)return null;let i=first(a|b);if(!at(a,i))[a,b]=[b,a];let k=at(a,i);a=scale(a,iv[k]);w=sc(w,k);b^=scale(a,at(b,i));if(!b)return null;let j=first(b),l=at(b,j);b=scale(b,iv[l]);w=sc(w,l);a^=scale(b,at(a,j));return [a,b,w]}
 const planes=t=>{let [a,b]=t;return [a,b,norm(a^b),norm(a^scale(b,2)),norm(a^scale(b,3))]};
 const align=(t,v)=>{let [a,b,w]=t,i=first(a),j=first(b),x=at(v,i),y=at(v,j);if((scale(a,x)^scale(b,y))!==v)throw Error("alignment");return x?[v,b,sc(w,iv[x])]:[v,a,sc(w,iv[y])]};
 const key=t=>t[0].toString(16)+":"+t[1].toString(16);
 const init=seed.map(([a,b,c])=>canon(BigInt(a),BigInt(b)<<24n,c));const clone=T=>T.map(x=>x.slice());
 function sig(T){let a=new Uint32Array(276),l=new Uint32Array(24);for(let [u,v,w] of T){let k=0;for(let i=0;i<24;i++){l[i]^=sc(w,sm(at(u,i),at(v,i)));for(let j=i+1;j<24;j++,k++)a[k]^=sc(w,sm(at(u,i),at(v,j))^sm(at(u,j),at(v,i)))}}return {a,l}}
 function wedge(a,b){let rows=Array(24).fill(0n);for(let i=0;i<24;i++)rows[i]=scale(b,at(a,i))^scale(a,at(b,i));return rows}
 function decompose(M){let a=M.slice(),res=[];for(let i=0;i<24;i++){if(!a[i])continue;let j=first(a[i]);if(i===j)throw Error("diagonal");let p=a[i],q=scale(a[j],iv[at(p,j)]);res.push([p,q]);let R=wedge(p,q);for(let k=0;k<24;k++)a[k]^=R[k];if(a[i]||a[j])throw Error("elim");}if(a.some(Boolean))throw Error("not zero");return res}
 const stat={proposals:steps,moves:0,flip:0,split:0,triple:0,pool:0,restarts:0,maxRank:33,mixedBest:0,best:33};
 function reduce(T){let changed=true;while(changed){changed=false;let keys=new Map(),weights=new Map();for(let i=0;i<T.length;i++){let t=T[i],k=key(t);if(keys.has(k)){let j=keys.get(k);T[j][2]^=t[2];T.splice(i,1);if(!T[j][2])T.splice(j,1);stat.pool++;changed=true;break}keys.set(k,i);let [w,s]=ow(t[2]);if(!weights.has(w))weights.set(w,[]);weights.get(w).push(i)}
 if(changed)continue;
 for(let [w,g] of weights){if(g.length<2)continue;
   let M=Array(24).fill(0n);for(let i of g){let t=T[i],[_,s]=ow(t[2]),a=wedge(scale(t[0],s),t[1]);for(let k=0;k<24;k++)M[k]^=a[k]}
   let parts=decompose(M);if(parts.length<g.length){let set=new Set(g);T=T.filter((_,i)=>!set.has(i)).concat(parts.map(([a,b])=>canon(a,b,w)));stat.pool+=g.length-parts.length;changed=true;break}
 }
 }return T}
 let state=s0>>>0;function rnd(n){state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)%n}
 let T=clone(init),best=clone(init),cap=38;
 const mixed=T=>T.filter(([a,b])=>((a&0xffffffn)&&(a>>24n))||((b&0xffffffn)&&(b>>24n))).length;
 function tryTriple(a,b,c,l,k){
   let P=wedge(a[0],a[1]),Q=wedge(b[0],b[1]),R=wedge(c[0],c[1]);
   let U=[a[0],a[1],b[0],b[1],c[0],c[1]];
   for(let trial=0;trial<6;trial++){
    let x=0n,y=0n;for(let u of U){x^=scale(u,rnd(4));y^=scale(u,rnd(4))}
    let z=canon(x,y,c[2]);if(!z)continue;
    let C=wedge(x,y),D=C.map((v,i)=>v^R[i]);if(!D.some(Boolean))continue;
    let A=P.map((v,i)=>v^scale(D[i],l)),B=Q.map((v,i)=>v^scale(D[i],k));
    // Fast rank <=2 test via one pivot pair, then exact reconstruction.
    let ra=decompose(A),rb=decompose(B);if(ra.length>1||rb.length>1)continue;
    return [...ra.map(([u,v])=>canon(u,v,a[2])),...rb.map(([u,v])=>canon(u,v,b[2])),z];
   }return null;
 }
 for(let iter=0;iter<steps;iter++){
   if(iter%6000===5999){T=clone(best);cap=33+[3,5,8,12][rnd(4)];stat.restarts++;continue}
   let G=new Map(),W=new Map();for(let i=0;i<T.length;i++){for(let v of planes(T[i])){let g=G.get(v)??[];g.push(i);G.set(v,g)}let [w]=ow(T[i][2]);let g=W.get(w)??[];g.push(i);W.set(w,g)}
   let mode=rnd(100),done=false;
   if(mode<20){for(let trial=0;trial<5;trial++){let i=rnd(T.length),j=rnd(T.length);if(i===j)continue;let l=1+rnd(3),k=1+rnd(3),w=sc(T[i][2],l)^sc(T[j][2],k),[v,s]=ow(w);if(!v)continue;let h=W.get(v);if(!h)continue;let z=h[rnd(h.length)];if(z===i||z===j)continue;let c=T[z].slice(),[_,t]=ow(c[2]);c[0]=scale(c[0],sm(t,iv[s]));c[2]=w;let R=tryTriple(T[i],T[j],c,l,k);if(R){T=T.filter((_,v)=>v!==i&&v!==j&&v!==z).concat(R);stat.triple++;done=true;break}}}
   if(!done&&mode<85){let g=[...G.entries()].filter(([_,v])=>v.length>1);if(g.length){let [v,h]=g[rnd(g.length)],i=h[rnd(h.length)],j=h[rnd(h.length)];if(i!==j){let a=align(T[i],v),b=align(T[j],v),k=1+rnd(3);let x=canon(v,a[1]^scale(b[1],k),a[2]),y=canon(v,b[1],b[2]^sc(a[2],k));T[i]=x;T[j]=y;T=T.filter(Boolean);stat.flip++;done=true}}}
   if(!done&&T.length<cap){let i=rnd(T.length),j=rnd(T.length);if(i!==j){let a=align(T[i],planes(T[i])[rnd(5)]),b=align(T[j],planes(T[j])[rnd(5)]),k=1+rnd(3);b[0]=scale(b[0],k);b[2]=sc(b[2],iv[k]);let P=canon(a[0],a[1]^b[0],a[2]),Q=canon(b[0],a[0]^b[1],a[2]),R=canon(b[0],b[1],a[2]^b[2]);T=T.filter((_,q)=>q!==i&&q!==j).concat([P,Q,R].filter(Boolean));stat.split++;done=true}}
   if(done){stat.moves++;T=reduce(T);stat.maxRank=Math.max(stat.maxRank,T.length);if(T.length<best.length||(T.length===best.length&&mixed(T)>mixed(best))){best=clone(T);stat.best=best.length;stat.mixedBest=mixed(best);if(best.length<33)break}}
 }
 const s=sig(init),b=sig(best),f=sig(T);if(!s.a.every((v,i)=>v===b.a[i]&&v===f.a[i]))throw Error("quadratic");
 return {stats:stat,best:best.length,terms:best.map(([a,b,w])=>[a.toString(16),b.toString(16),w]),squareCorrection:Array.from(s.l,(x,i)=>x^b.l[i]),quadraticWords:276}
}
const seeds=process.argv.slice(2,4).map(f=>JSON.parse(fs.readFileSync(f,'utf8')));const R=[];for(let k=0;k<2;k++)for(let i=0;i<2;i++)R.push({type:i,seed:k,...mixedF4(seeds[k][i].terms,Number(process.argv[4]||60000),0x1735a23+113*i+719*k)});fs.writeFileSync('mixed_f4_results.json',JSON.stringify(R,null,2));console.log(R.map(({terms,squareCorrection,...r})=>({...r,squareWords:squareCorrection.filter(Boolean).length})));
