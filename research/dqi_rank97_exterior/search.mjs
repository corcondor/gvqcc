// Exact mixed-control exterior-plane search; normalized #311 tensors.
import fs from 'node:fs';
function decode(s){
 const alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";let data=[],acc=0,bits=0;for(const ch of s.replace(/\s/g,"")){if(ch==="=")break;acc=(acc<<6)|alphabet.indexOf(ch);bits+=6;if(bits>=8){bits-=8;data.push(acc>>bits&255)}}
 let off=2,bit=0;const read=n=>{let v=0;for(let j=0;j<n;j++){v|=((data[off]>>bit)&1)<<j;if(++bit===8){bit=0;off++}}return v};
 function huff(lengths){let c=new Uint32Array(16),next=new Uint32Array(16),maps=Array.from({length:16},()=>new Map());for(let n of lengths)if(n)c[n]++;let code=0;for(let i=1;i<16;i++){code=(code+c[i-1])*2;next[i]=code}for(let i=0;i<lengths.length;i++){let n=lengths[i];if(n)maps[n].set(next[n]++,i)}return maps}
 function sym(tree){let code=0;for(let n=1;n<16;n++){code=(code<<1)|read(1);if(tree[n].has(code))return tree[n].get(code)}throw Error("invalid huffman")}
 const lb=[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258],le=[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0],db=[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577],de=[0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13];
 let out=[],last=0;while(!last){last=read(1);let type=read(2);if(type===0){if(bit){off++;bit=0}let n=read(16);if((read(16)^65535)!==n)throw Error("stored");while(n--)out.push(read(8));continue}let L,D;if(type===1){L=huff(Array.from({length:288},(_,i)=>i<144?8:i<256?9:i<280?7:8));D=huff(Array(32).fill(5))}else if(type===2){let nl=read(5)+257,nd=read(5)+1,nc=read(4)+4;let order=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15],cl=Array(19).fill(0);for(let i=0;i<nc;i++)cl[order[i]]=read(3);let ct=huff(cl),lens=[];while(lens.length<nl+nd){let a=sym(ct);if(a<16)lens.push(a);else{let n=a===16?read(2)+3:a===17?read(3)+3:read(7)+11,v=a===16?lens[lens.length-1]:0;while(n--)lens.push(v)}}L=huff(lens.slice(0,nl));D=huff(lens.slice(nl))}else throw Error("type");while(true){let a=sym(L);if(a<256){out.push(a);continue}if(a===256)break;a-=257;let n=lb[a]+read(le[a]),d=sym(D),dist=db[d]+read(de[d]);while(n--)out.push(out[out.length-dist])}}
 if(out.length!==3564)throw Error(out.length);let nums=[];for(let i=0;i<out.length;i+=3)nums.push(out[i]|out[i+1]<<8|out[i+2]<<16);let T=[];for(let i=0;i<nums.length;i+=297){let ts=[];for(let j=i;j<i+297;j+=3)ts.push(nums.slice(j,j+3));T.push(ts)}return T
}
function experiment(T, steps=16000,seed=9917){
 let rng=seed>>>0;function rnd(n){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return (rng>>>0)%n}
 const canon=(a,b,w)=>{if(!a||!b||a===b||!w)return null;let c=a^b;if(a>b)[a,b]=[b,a];if(c<a){b=a;a=c}else if(c<b)b=c;return [a,b,w]};
 const vectors=t=>[t[0],t[1],t[0]^t[1]];
 const key=t=>t[0].toString(16)+":"+t[1].toString(16);
 const has=(t,v)=>t[0]===v||t[1]===v||(t[0]^t[1])===v;
 const other=(t,v)=>t[0]===v?t[1]:t[0];
 const pc=(x)=>{let n=0;while(x){x&=x-1;n++}return n};
 const bp=Array.from({length:48},(_,i)=>1n<<BigInt(i));
 function signature(S){let A=new Uint32Array(48*48),lin=new Uint32Array(48);for(const [a,b,w] of S){for(let i=0;i<48;i++){if((a&bp[i])&&(b&bp[i]))lin[i]^=w;for(let j=i+1;j<48;j++)if(Boolean(a&bp[i])&&Boolean(b&bp[j])!==false){/* handled below independently */}for(let j=i+1;j<48;j++)if((Boolean(a&bp[i])&&Boolean(b&bp[j]))!==(Boolean(b&bp[i])&&Boolean(a&bp[j])))A[i*48+j]^=w}}return {A,lin}}
 let reductions=0;
 function merge(S){let again=true;while(again){again=false;let seen=new Map(),ws=new Map();for(let i=0;i<S.length;i++){let t=S[i],k=key(t);if(seen.has(k)){let j=seen.get(k);S[j][2]^=t[2];S.splice(i,1);if(!S[j][2])S.splice(j,1);again=true;reductions++;break}seen.set(k,i);let group=ws.get(t[2])??[];for(let j of group){let v=vectors(t).find(v=>has(S[j],v));if(v!==undefined){let a=canon(v,other(t,v)^other(S[j],v),t[2]);S.splice(i,1);if(a)S[j]=a;else S.splice(j,1);again=true;reductions++;break}}if(again)break;group.push(i);ws.set(t[2],group)}}return S}
 // Small-span wedge coordinates. Enumerate every plane in dim <=6 once.
 const dictionaries=new Map();
 function dict(d){if(dictionaries.has(d))return dictionaries.get(d);let W=new Map(),z=[];function wedge(a,b){let v=0,k=0;for(let i=0;i<d;i++)for(let j=i+1;j<d;j++,k++)if((((a>>i)&(b>>j)&1)^((b>>i)&(a>>j)&1)))v|=1<<k;return v}for(let a=1;a<1<<d;a++)for(let b=a+1;b<1<<d;b++)if((a^b)>b){let w=wedge(a,b);W.set(w,[a,b]);z.push(w)}const o={W,z,wedge};dictionaries.set(d,o);return o}
 function coords(vs){let base=[],rows=new Map();for(let v of vs){let x=v,mask=0;while(x){let k=x.toString(2).length-1;if(!rows.has(k)){const j=base.length;base.push(v);rows.set(k,[x,mask^(1<<j)]);break}let [p,c]=rows.get(k);x^=p;mask^=c}}function from(v){let x=0n;for(let j=0;j<base.length;j++)if(v>>j&1)x^=base[j];return x}function to(v){let x=v,mask=0;while(x){let [p,c]=rows.get(x.toString(2).length-1);x^=p;mask^=c}return mask}return {base,from,to}}
 function tri(t,u,v){let c=coords([t[0],t[1],u[0],u[1],v[0],v[1]]),{W,z,wedge}=dict(c.base.length),get=t=>wedge(c.to(t[0]),c.to(t[1]));let x=get(t)^get(v),y=get(u)^get(v),cur=get(v),start=rnd(z.length);
   for(let k=0;k<z.length;k++){let p=z[(start+k)%z.length];if(p===cur)continue;let q=x^p,h=y^p;if(!W.has(q)||!W.has(h))continue;const term=(w,v)=>{let [a,b]=W.get(w);return canon(c.from(a),c.from(b),v)};return [term(q,t[2]),term(h,u[2]),term(p,v[2])]}return null}
 const initial=T.map(([a,b,w])=>canon(BigInt(a),BigInt(b)<<24n,w));let S=initial.map(t=>t.slice()),best=S.map(t=>t.slice()),stat={moves:0,triple:0,split:0,flip:0,restarts:0,mixedMax:0},limit=104;
 for(let iter=0;iter<steps;iter++){
  if(iter%2000===1999){S=best.map(t=>t.slice());stat.restarts++;continue}
  const factors=new Map(),weights=new Map();for(let i=0;i<S.length;i++){for(let a of vectors(S[i])){let g=factors.get(a)??[];g.push(i);factors.set(a,g)}let g=weights.get(S[i][2])??[];g.push(i);weights.set(S[i][2],g)}
  let t=rnd(100),changed=false;
  if(t<50){let a=rnd(S.length),b=rnd(S.length);if(a!==b){let w=S[a][2]^S[b][2],g=weights.get(w);if(g&&w){let c=g[rnd(g.length)];if(c!==a&&c!==b){let v=tri(S[a],S[b],S[c]);if(v){S[a]=v[0];S[b]=v[1];S[c]=v[2];stat.triple++;changed=true}}}}}
  if(!changed&&t<90){let a=rnd(S.length),v=vectors(S[a])[rnd(3)],g=factors.get(v);if(g.length>1){let b=g[rnd(g.length)];if(a!==b){let A=S[a],B=S[b],q=canon(v,other(A,v)^other(B,v),A[2]),h=canon(v,other(B,v),A[2]^B[2]);if(q&&h){S[a]=q;S[b]=h;changed=true;stat.flip++}}}}
  if(!changed&&S.length<limit){let a=rnd(S.length),b=rnd(S.length);if(a!==b){let A=S[a],v=vectors(A)[rnd(3)],w=other(A,v),c=vectors(S[b])[rnd(3)],q=canon(v,w^c,A[2]),h=canon(v,c,A[2]);if(q&&h){S[a]=q;S.push(h);stat.split++;changed=true}}}
  if(changed){stat.moves++;merge(S);if(S.length<best.length)best=S.map(t=>t.slice());if((iter%100)===0)stat.mixedMax=Math.max(stat.mixedMax,S.filter(t=>t.slice(0,2).some(v=>(v&0xffffffn)!==0n&&(v>>24n)!==0n)).length)}
 }
 const before=signature(initial),after=signature(S),bestsig=signature(best);if(!before.A.every((v,i)=>v===after.A[i])||!before.A.every((v,i)=>v===bestsig.A[i]))throw Error("quadratic mismatch");
 return {steps,best:best.length,final:S.length,stat,reductions,quadraticChecks:1128,linearCorrectionRank:bestsig.lin.filter((v,i)=>v!==before.lin[i]).length,bestTerms:best.map(([a,b,w])=>[a.toString(16),b.toString(16),w])};
}
const T=decode(fs.readFileSync(process.argv[2],'utf8'));
const result=T.map((t,i)=>experiment(t,Number(process.argv[3]||18000),9917+i*101));
fs.writeFileSync('mixed_results.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result.map(({bestTerms,...r})=>r)));
