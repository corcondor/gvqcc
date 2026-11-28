import fs from 'node:fs';
function search(init,steps,seed){
 let rng=seed>>>0;function rnd(n){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return (rng>>>0)%n}
 const canon=(a,b,w)=>{if(!a||!b||a===b||!w)return null;let c=a^b;if(a>b)[a,b]=[b,a];if(c<a){b=a;a=c}else if(c<b)b=c;return [a,b,w]};
 const vectors=t=>[t[0],t[1],t[0]^t[1]],has=(t,v)=>t[0]===v||t[1]===v||(t[0]^t[1])===v,other=(t,v)=>t[0]===v?t[1]:t[0],key=t=>t[0].toString(16)+":"+t[1].toString(16);
 const bp=Array.from({length:48},(_,i)=>1n<<BigInt(i));
 function sig(S){let a=new Uint32Array(1128),l=new Uint32Array(48);for(const [x,y,w] of S){let k=0;for(let i=0;i<48;i++){if(x&y&bp[i])l[i]^=w;for(let j=i+1;j<48;j++,k++)if((!!(x&bp[i])&&!!(y&bp[j]))!==(!!(y&bp[i])&&!!(x&bp[j])))a[k]^=w}}return {a,l}}
 let reductions=0;function merge(S){let again=true;while(again){again=false;let seen=new Map(),ws=new Map();for(let i=0;i<S.length;i++){let t=S[i],k=key(t);if(seen.has(k)){let j=seen.get(k);S[j][2]^=t[2];S.splice(i,1);if(!S[j][2])S.splice(j,1);again=true;reductions++;break}seen.set(k,i);let group=ws.get(t[2])??[];for(let j of group){let v=vectors(t).find(v=>has(S[j],v));if(v!==undefined){let a=canon(v,other(t,v)^other(S[j],v),t[2]);S.splice(i,1);if(a)S[j]=a;else S.splice(j,1);again=true;reductions++;break}}if(again)break;group.push(i);ws.set(t[2],group)}}return S}
 const dictionaries=new Map();
 function dict(d){if(dictionaries.has(d))return dictionaries.get(d);let W=new Map(),z=[];function wedge(a,b){let v=0,k=0;for(let i=0;i<d;i++)for(let j=i+1;j<d;j++,k++)if((((a>>i)&(b>>j)&1)^((b>>i)&(a>>j)&1)))v|=1<<k;return v}for(let a=1;a<1<<d;a++)for(let b=a+1;b<1<<d;b++)if((a^b)>b){let w=wedge(a,b);W.set(w,[a,b]);z.push(w)}const o={W,z,wedge};dictionaries.set(d,o);return o}
 function coords(vs){let base=[],rows=new Map();for(let v of vs){let x=v,mask=0;while(x){let k=x.toString(2).length-1;if(!rows.has(k)){const j=base.length;base.push(v);rows.set(k,[x,mask^(1<<j)]);break}let [p,c]=rows.get(k);x^=p;mask^=c}}function from(v){let x=0n;for(let j=0;j<base.length;j++)if(v>>j&1)x^=base[j];return x}function to(v){let x=v,mask=0;while(x){let [p,c]=rows.get(x.toString(2).length-1);x^=p;mask^=c}return mask}return {base,from,to}}
 function tri(t,u,v){let c=coords([t[0],t[1],u[0],u[1],v[0],v[1]]),{W,z,wedge}=dict(c.base.length),get=t=>wedge(c.to(t[0]),c.to(t[1]));let x=get(t)^get(v),y=get(u)^get(v),cur=get(v),start=rnd(z.length);for(let k=0;k<z.length;k++){let p=z[(start+k)%z.length];if(p===cur)continue;let q=x^p,h=y^p;if(!W.has(q)||!W.has(h))continue;const term=(w,v)=>{let [a,b]=W.get(w);return canon(c.from(a),c.from(b),v)};return [term(q,t[2]),term(h,u[2]),term(p,v[2])]}return null}
 let S=init.map(t=>t.slice()),best=S.map(t=>t.slice()),stats={moves:0,compound:0,triple:0,shared:0,restarts:0,maxRank:99,mixedMax:0,lowerHits:0},limit=103;
 const clone=S=>S.map(t=>t.slice());
 for(let k=0;k<steps;k++){
   if(k%4000===3999){S=clone(best);stats.restarts++;continue}
   let f=new Map(),w=new Map();for(let i=0;i<S.length;i++){for(let a of vectors(S[i])){let g=f.get(a)??[];g.push(i);f.set(a,g)}let g=w.get(S[i][2])??[];g.push(i);w.set(S[i][2],g)}
   let t=rnd(100),moved=false;
   if(t<40){for(let atry=0;atry<6;atry++){let a=rnd(S.length),b=rnd(S.length);if(a===b)continue;let g=w.get(S[a][2]^S[b][2]);if(!g)continue;let c=g[rnd(g.length)];if(c===a||c===b)continue;let z=tri(S[a],S[b],S[c]);if(z){S[a]=z[0];S[b]=z[1];S[c]=z[2];stats.triple++;moved=true;break}}}
   if(!moved&&t<85){let share=[...f.values()].filter(g=>g.length>1);if(share.length){let g=share[rnd(share.length)],a=g[rnd(g.length)],b=g[rnd(g.length)];if(a!==b){let A=S[a],B=S[b],v=vectors(A).find(v=>has(B,v)),q=canon(v,other(A,v)^other(B,v),A[2]),h=canon(v,other(B,v),A[2]^B[2]);if(q){S[a]=q;if(h)S[b]=h;else S.splice(b,1);stats.shared++;moved=true}}}}
   if(!moved&&S.length<limit){
     let i=rnd(S.length),j=rnd(S.length);
     if(i!==j){let A=S[i],B=S[j],a=vectors(A)[rnd(3)],b=other(A,a),c=vectors(B)[rnd(3)],d=other(B,c);
       // Split + flip as one move, not immediate cancellation:
       // (a∧b)u+(c∧d)v = [a∧(b+c)]u + [c∧(a+d)]u + [c∧d](u+v).
       let P=canon(a,b^c,A[2]),Q=canon(c,a^d,A[2]),R=canon(c,d,A[2]^B[2]);
       if(P&&Q&&R){S[i]=P;S[j]=Q;S.push(R);stats.compound++;moved=true}
     }
   }
   if(moved){stats.moves++;merge(S);if(S.length<best.length){best=clone(S);stats.lowerHits++}stats.maxRank=Math.max(stats.maxRank,S.length);if(k%100===0)stats.mixedMax=Math.max(stats.mixedMax,S.filter(t=>t.slice(0,2).some(v=>(v&0xffffffn)!==0n&&(v>>24n)!==0n)).length)}
 }
 let a=sig(init),b=sig(S),c=sig(best);if(!a.a.every((v,i)=>v===b.a[i]&&v===c.a[i]))throw Error("signature");
 return {steps,best:best.length,final:S.length,stats,reductions,quadraticCoefficients:1128,linearCorrection:Array.from(c.l,(x,i)=>x^a.l[i]),bestTerms:best.map(([a,b,w])=>[a.toString(16),b.toString(16),w])};
}
const T=JSON.parse(fs.readFileSync(process.argv[2],'utf8')).map(x=>x.bestTerms.map(([a,b,w])=>[BigInt("0x"+a),BigInt("0x"+b),w]));
const R=T.map((t,i)=>search(t,Number(process.argv[3]||60000),53197+i*1337));
fs.writeFileSync('compound_results.json',JSON.stringify(R,null,2));console.log(JSON.stringify(R.map(({bestTerms,linearCorrection,...x})=>x)));
