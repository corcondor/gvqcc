
const NV=1219, FULL=(1n<<1219n)-1n;
const alpha="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_"+String.fromCharCode(96)+"{|}~";
function assert(x,m){if(!x)throw Error(m||"assertion failed")}
function b85(s){s=s.replace(/\s/g,"");const a=new Map([...alpha].map((c,i)=>[c,i]));const n=s.length;let out=[];for(let i=0;i<n;i+=5){let v=0;for(let j=0;j<5;j++)v=v*85+(i+j<n?a.get(s[i+j]):84);assert(Number.isFinite(v)&&v<4294967296,"b85");for(let j=0;j<Math.min(4,n-i-1);j++)out.push((v>>>((3-j)*8))&255)}return Uint8Array.from(out)}
function inflate(z){
 let bit=16, out=[];function get(n){let v=0;for(let i=0;i<n;i++,bit++)v|=((z[bit>>3]>>(bit&7))&1)<<i;return v}
 function huff(lens){let cnt=Array(16).fill(0),next=Array(16).fill(0),maps=Array.from({length:16},()=>new Map());for(let l of lens)if(l)cnt[l]++;let c=0;for(let l=1;l<16;l++){c=(c+cnt[l-1])<<1;next[l]=c}for(let i=0;i<lens.length;i++){let l=lens[i];if(l)maps[l].set(next[l]++,i)}return maps}
 function dec(h){let c=0;for(let l=1;l<16;l++){c=c*2+get(1);if(h[l].has(c))return h[l].get(c)}throw Error("huffman")}
 const lb=[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258];
 const le=[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0];
 const db=[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577];
 let last=0;while(!last){last=get(1);let typ=get(2),lh,dh;if(typ===0){bit=(bit+7)&~7;let n=get(16);assert((n^65535)===get(16),"stored");for(let i=0;i<n;i++)out.push(get(8));continue}
 if(typ===1){lh=huff(Array.from({length:288},(_,i)=>i<144?8:i<256?9:i<280?7:8));dh=huff(Array(32).fill(5))}
 else if(typ===2){let nl=get(5)+257,nd=get(5)+1,nc=get(4)+4,cl=Array(19).fill(0),order=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15];for(let i=0;i<nc;i++)cl[order[i]]=get(3);let ch=huff(cl),ll=[];while(ll.length<nl+nd){let t=dec(ch);if(t<16)ll.push(t);else{let n=t===16?3+get(2):t===17?3+get(3):11+get(7),v=t===16?ll.at(-1):0;while(n--)ll.push(v)}}assert(ll.length===nl+nd,"lengths");lh=huff(ll.slice(0,nl));dh=huff(ll.slice(nl))}
 else throw Error("type");
 while(true){let t=dec(lh);if(t<256){out.push(t);continue}if(t===256)break;let i=t-257,n=lb[i]+get(le[i]);let d=dec(dh),dist=db[d]+get(d<4?0:(d>>1)-1);assert(dist<=out.length&&n<=258,"distance");while(n--)out.push(out[out.length-dist]);}}
 let a=1,b=0;for(let v of out){a=(a+v)%65521;b=(b+a)%65521}let n=z.length;assert(((b<<16)|a)===((z[n-4]<<24)|(z[n-3]<<16)|(z[n-2]<<8)|z[n-1]),"adler");return Uint8Array.from(out)
}
const qmask=(i)=>1n<<BigInt(i);
function pack(fn,n=NV){let v=0n;for(let a=n-1;a>=0;a--)v=(v<<1n)|BigInt(+!!fn(a));return v}
function bits(v){let b=[];while(v){let t=v&-v;b.push(t.toString(2).length-1);v^=t}return b}
function bx(v,f){let r=0n;for(let i of bits(v))r^=f[i];return r}
function bigbits(b,n){let v=0n;for(let i=0;i<n;i++)if(b[i>>3]&(128>>(i&7)))v|=qmask(i);return v}
function basis(){const p=new Map();return {p,red(v,c=0n){while(v){const t=v.toString(2).length-1,e=p.get(t);if(!e)break;v^=e[0];c^=e[1]}return [v,c]},add(v,c=0n){let [r,s]=this.red(v,c);if(r){p.set(r.toString(2).length-1,[r,s]);return true}return false},expr(v){let [r,c]=this.red(v);assert(!r,"not in span");return c}}}
const A=Array.from({length:11},(_,i)=>pack(a=>(a>>i)&1));
const L=A.slice(0,4),QUADS=[[0,1],[0,2],[1,2],[0,3],[1,3]],TAGS=QUADS.map(([i,j])=>L[i]&L[j]),LOWS=[L[2]&L[3],L[0]&L[1]&L[2],L[0]&L[1]&L[3],L[0]&L[2]&L[3],L[1]&L[2]&L[3],L[0]&L[1]&L[2]&L[3]];
const SEL=Array.from({length:11},(_,i)=>i),WQ=Array.from({length:35},(_,i)=>11+i),OUTQ=Array.from({length:30},(_,i)=>11+Math.floor(i/6)*7+i%6);
function decodeFixture(s){
 const j=JSON.parse(s),v=inflate(b85(j.payload));assert(v.length===NV*75+150,"fixture size");
 const W=Array.from({length:NV},(_,a)=>Array.from(v.slice(a*75,a*75+75)));
 const E=Array.from({length:75},(_,i)=>[v[NV*75+2*i],v[NV*75+2*i+1]]);
 return {W,E,raw_sha:j.raw_sha256};
}
function decodePrograms(s){
 let blob=b85(s),pos=0,ret={};function take(n){let a=blob.slice(pos,pos+n);pos+=n;assert(a.length===n,"payload len");return a}
 const KS=[[2,132,4,9],[3,130,7,14],[4,131,3,7],[6,131,4,11],[8,123,11,4],[9,130,13,7],[10,130,7,6],[12,127,6,8],[13,124,11,3],[14,124,6,9]],BS=[[1,20743],[5,20947],[7,20978],[11,20826]];
 for(let [k,n,c1,c2] of KS){let ands=Array.from({length:68},()=>[...take(6)]),B=Array.from({length:8},()=>bigbits(take(10),77)),U=Array.from({length:n},()=>bigbits(take(13),99)),V=Array.from({length:n},()=>bigbits(take(13),99)),M=Array.from({length:n},()=>Number(bigbits(take(4),30))),R=Array.from({length:30},()=>bigbits(take(13),99));ret[k]={k,ands,B,U,V,M,R,c1,c2}}
 for(let [k,n] of BS)ret[k]={k,window:inflate(take(n))};assert(pos===blob.length,"program size");return ret
}
function features(P){
 let f=[FULL,...A,...TAGS],gens=Array.from({length:7},(_,i)=>pack(a=>(a>>i)&1,77));
 for(let row of P.ands){let u=0n,v=0n;for(let i of row.slice(0,3))if(i<255)u^=gens[i];for(let i of row.slice(3))if(i<255)v^=gens[i];gens.push(u&v);f.push(pack(a=>((u&v)>>BigInt(a>>4))&1n))}
 f.push(...LOWS);for(let i=0;i<8;i++)f.push(pack(a=>((a&15)===(i<4?P.c1:P.c2))&&((P.B[i]>>BigInt(a>>4))&1n)));
 assert(f.length===99);return f
}
function buildRegular(P){
 let ops=[],f=[FULL,...A,...TAGS],names=[-1,...SEL,...Array.from({length:5},(_,j)=>WQ[7*j+6])],lin=basis(),recs=[],free=46;
 for(let i=0;i<f.length;i++)lin.add(f[i],qmask(i));
 for(let j=0;j<5;j++)ops.push(["CX",WQ[7*j+5],WQ[7*j+6]]);
 function fs(v){let q=lin.expr(v);return [bits(q>>1n).map(i=>names[i+1]),!!(q&1n)]}
 function ctl(su,cu,sv,cv){
  let qa,qb,s2,inA;for(let a of su.slice().sort((a,b)=>a-b)){qa=a;inA=sv.includes(qa);s2=inA?[...new Set([...sv,...su])].filter(x=>sv.includes(x)!==su.includes(x)):sv;let cand=s2.filter(x=>x!==qa);if(cand.length){qb=Math.min(...cand);break}}
  assert(qb!==undefined,"control independent");let pre=su.filter(x=>x!==qa).sort((a,b)=>a-b).map(x=>["CX",x,qa]);if(cu)pre.push(["X",qa]);pre.push(...s2.filter(x=>x!==qb&&x!==qa).sort((a,b)=>a-b).map(x=>["CX",x,qb]));if(inA)pre.push(["CX",qa,qb]);if(cv!== (inA?cu:false))pre.push(["X",qb]);return [pre,qa,qb]
 }
 const rev=a=>a.slice().reverse();
 function calc(u,v,track=true){let [pre,a,b]=ctl(...fs(u),...fs(v)),q=free++;assert(q<128);ops.push(...pre,["CCX",a,b,q],...rev(pre));recs.push([pre,a,b,q]);names.push(q);f.push(u&v);if(track)lin.add(u&v,qmask(f.length-1))}
 let gens=Array.from({length:7},(_,i)=>pack(a=>(a>>i)&1,77));for(let row of P.ands){let u=0n,v=0n;for(let i of row.slice(0,3))if(i<255)u^=gens[i];for(let i of row.slice(3))if(i<255)v^=gens[i];gens.push(u&v);calc(pack(a=>(u>>BigInt(a>>4))&1n),pack(a=>(v>>BigInt(a>>4))&1n))}
 for(let [u,v] of [[L[2],L[3]],[L[0]&L[1],L[2]],[L[0]&L[1],L[3]],[L[0]&L[2],L[3]],[L[1]&L[2],L[3]],[L[0]&L[1]&L[2],L[3]]])calc(u,v);
 for(let i=0;i<8;i++)calc(pack(a=>(a&15)===(i<4?P.c1:P.c2)),pack(a=>(P.B[i]>>BigInt(a>>4))&1n),false);
 assert(f.every((x,i)=>x===features(P)[i]),"feature mismatch");
 function sup(v){return [bits(v>>1n).map(i=>names[i+1]),!!(v&1n)]}
 for(let i=0;i<P.M.length;i++)if(P.M[i]){let [pre,a,b]=ctl(...sup(P.U[i]),...sup(P.V[i])),ts=bits(BigInt(P.M[i])).map(j=>OUTQ[j]),fan=ts.slice(1).map(t=>["CX",ts[0],t]);ops.push(...pre,...fan,["CCX",a,b,ts[0]],...rev(fan),...rev(pre))}
 for(let j=0;j<30;j++){let [s,c]=sup(P.R[j]);ops.push(...s.sort((a,b)=>a-b).map(q=>["CX",q,OUTQ[j]]));if(c)ops.push(["X",OUTQ[j]])}
 for(let [pre,a,b,q] of rev(recs))ops.push(...pre,["HMR",q],["CZ",a,b],...rev(pre));
 for(let j=4;j>=0;j--)ops.push(["CX",WQ[7*j+5],WQ[7*j+6]]);
 return ops;
}
function buildWindow(P){
 let b=P.window,ops=[],i=0,first;for(let j=0;j<5;j++)ops.push(["CX",WQ[7*j+5],WQ[7*j+6]]);
 function sup(p){let x=bigbits(b.slice(p,p+17),129);return [bits(x&((1n<<128n)-1n)),!!(x>>128n)]}
 function ctl(su,cu,sv,cv){let qa,qb,s2,inA;for(let a of su){qa=a;inA=sv.includes(qa);s2=inA?[...new Set([...sv,...su])].filter(x=>sv.includes(x)!==su.includes(x)):sv;let cand=s2.filter(x=>x!==qa);if(cand.length){qb=Math.min(...cand);break}}assert(qb!==undefined);let pre=su.filter(x=>x!==qa).sort((a,b)=>a-b).map(x=>["CX",x,qa]);if(cu)pre.push(["X",qa]);pre.push(...s2.filter(x=>x!==qb&&x!==qa).sort((a,b)=>a-b).map(x=>["CX",x,qb]));if(inA)pre.push(["CX",qa,qb]);if(cv!==(inA?cu:false))pre.push(["X",qb]);return [pre,qa,qb]}
 const rev=a=>a.slice().reverse(),u32=p=>(b[p]|(b[p+1]<<8)|(b[p+2]<<16)|(b[p+3]<<24))>>>0;
 while(b[i]!==3){if(b[i]<2){let p=i+(b[i]===0?2:5),[pre,a,c]=ctl(...sup(p),...sup(p+17));if(!b[i]){let q=b[i+1];ops.push(...pre,["CCX",a,c,q],...rev(pre));if(!first)first=[q,a,c]}else{let ts=bits(BigInt(u32(i+1))).map(j=>OUTQ[j]),fan=ts.slice(1).map(t=>["CX",ts[0],t]);ops.push(...pre,...fan,["CCX",a,c,ts[0]],...rev(fan),...rev(pre))}i=p+34}
 else{assert(b[i]===2);let q=b[i+1],m=u32(i+2),n=b[i+40]|(b[i+41]<<8);ops.push(...sup(i+6)[0].map(r=>["CX",q,r]),...bits(BigInt(m)).map(j=>["CX",q,OUTQ[j]]),["HMR",q]);for(let j=0;j<n;j++)ops.push(["CZ",b[i+42+2*j],b[i+43+2*j]]);for(let r of sup(i+23)[0])ops.push(["Z",r]);i+=42+2*n}}
 for(let j=0;j<30;j++){let [s,c]=sup(i+1+17*j);ops.push(...s.map(q=>["CX",q,OUTQ[j]]));if(c)ops.push(["X",OUTQ[j]])}
 ops.push(["HMR",first[0]],["CZ",first[1],first[2]]);for(let j=4;j>=0;j--)ops.push(["CX",WQ[7*j+5],WQ[7*j+6]]);return ops
}
function bankWords(W,k){return Array.from({length:35},(_,j)=>pack(a=>(W[a][5*k+Math.floor(j/7)]>>(j%7))&1))}
function replay(ops,initial){
 let q=[...A,...initial,...Array(82).fill(0n)],phase=0n,hm=0,n=0;for(let [t,a,b,c] of ops){if(t==="X")q[a]^=FULL;else if(t==="CX")q[b]^=q[a];else if(t==="CCX"){q[c]^=q[a]&q[b];n++}else if(t==="HMR"){assert(!phase,"phase debt at HMR");phase=q[a];q[a]=0n;hm++}else if(t==="CZ"){phase^=q[a]&q[b]}else if(t==="Z")phase^=q[a];else throw Error(t)}
 assert(!phase,"phase debt terminal");assert(q.slice(0,11).every((x,i)=>x===A[i]),"selection");assert(q.slice(46).every(x=>x===0n),"scratch");return {words:q.slice(11,46),n,hm,ops:ops.length}
}
function cares(W,E){
 let non=Array.from({length:76},(_,i)=>i===0?FULL:0n),C=[];for(let r=0;r<75;r++){let [p,c]=E[r];assert(non[c]===0n,"not tree "+r);C.push(non[p]);let cos=pack(a=>W[a][r]%64!==32),sin=pack(a=>W[a][r]%64!==0);non[c]=non[p]&sin;non[p]&=cos}return C
}
function inspect(fix,payload){
 let {W,E}=decodeFixture(fix),P=decodePrograms(payload),C=cares(W,E),cur=bankWords(W,0),rows=[cur],stats=[],opMap={};
 for(let k=1;k<=14;k++){
  assert(TAGS.every((v,j)=>(cur[j*7+5]^cur[j*7+6])===v),"tag k="+k);
  let op=P[k].window?buildWindow(P[k]):buildRegular(P[k]);opMap[k]=op;
  let r=replay(op,cur),back=replay(op,r.words);assert(back.words.every((v,i)=>v===cur[i]),"reverse "+k);
  let ref=bankWords(W,k),bad=0n,changed=0;for(let j=0;j<5;j++){let diff=0n;for(let b=0;b<7;b++)diff|=r.words[7*j+b]^ref[7*j+b];bad|=diff&C[5*k+j];changed+=bits(diff).length}
  stats.push({k,n:r.n,hm:r.hm,ops:r.ops,changed,bad:bits(bad).length});assert(!bad,"physics mismatch "+k);cur=r.words;rows.push(cur)
 }
 return {P,C,rows,stats,opMap,W,E}
}
return {b85,inflate,decodeFixture,decodePrograms,features,buildRegular,buildWindow,replay,cares,inspect,basis,bits,bx,pack,qmask,NV,FULL,OUTQ,TAGS,A,WQ};
