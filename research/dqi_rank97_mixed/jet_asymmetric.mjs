
import assert from 'node:assert/strict';
// Exact asymmetric bilinear local search for GF(4)[e]/(e^2).
// For d>=2, a shorter decomposition can be padded by splitting an output column.
const parity=x=>{let z=0;while(x){z^=1;x&=x-1}return z};
const pop=x=>{let z=0;while(x){z++;x&=x-1}return z};
const gf=(a,b)=>{let x=0;while(b){if(b&1)x^=a;b>>=1;a<<=1;if(a&4)a^=7}return x};
const mul=(x,y)=>gf(x&3,y&3)|((gf(x&3,y>>2)^gf(x>>2,y&3))<<2);
const outer=(a,b)=>[0,1,2,3].reduce((s,j)=>s|(((b>>j)&1?a:0)<<(4*j)),0);
const app=(M,x)=>[0,1,2,3].reduce((s,j)=>s^(((x>>j)&1)?(M>>(4*j))&15:0),0);
const compose=(A,B)=>[0,1,2,3].reduce((s,j)=>s|(app(A,(B>>(4*j))&15)<<(4*j)),0);
const rank=a=>{let bas=[0,0,0,0],n=0;for(let j=0;j<4;j++){let x=(a>>(4*j))&15;for(let k=3;k>=0&&x;k--)if((x>>k)&1){if(bas[k])x^=bas[k];else{bas[k]=x;n++;break}}}return n};
const ranks=Uint8Array.from({length:65536},(_,i)=>rank(i));
let raw=Array.from({length:16},(_,f)=>{let z=0;for(let i=0;i<4;i++)for(let j=0;j<4;j++)if(parity(f&mul(1<<i,1<<j)))z|=1<<(i+4*j);return z});
for(let f=1;f<16;f++)assert.equal(ranks[raw[f]],f<4?2:4);
let bases=[];
for(let a=1;a<16;a++)for(let b=1;b<16;b++)if(a!==b)for(let c=1;c<16;c++)if(![a,b,a^b].includes(c))for(let d=1;d<16;d++)if(![a,b,a^b,c,a^c,b^c,a^b^c].includes(d)){let v=[a,b,c,d],r=[];for(let i=0;i<4;i++){let t=1;while(!v.every((u,j)=>parity(u&t)===(i===j?1:0)))t++;r.push(outer(v[i],t));}bases.push(r)}
assert.equal(bases.length,20160);
let R=[];for(let a=1;a<16;a++)for(let b=1;b<16;b++)R.push(outer(a,b));
let subs=new Set([1]);for(let i=1;i<16;i++)for(let s of [...subs]){let t=s;for(let j=0;j<16;j++)if(s>>j&1)t|=1<<(j^i);subs.add(t)}
assert.equal(subs.size,67);
const span=vs=>{let s=[0];for(let v of vs)s.push(...s.map(x=>x^v));return s};
// The unit orbit is exactly the twelve full-rank covectors.
let orbit=new Set();for(let u=1;u<16;u++)if(u&3){let A=0;for(let j=0;j<4;j++)A|=mul(u,1<<j)<<(4*j);orbit.add(compose(raw[4],A))}
assert.equal(orbit.size,12);assert(raw.slice(4).every(x=>orbit.has(x)));
let stats={};
for(let s of subs){let d=Math.log2(pop(s)),e=d-Math.log2(pop(s&15));if(!((d===2&&e===1)||(d===3&&e>=1)||(d===4&&e===2)))continue;
let key=d+':'+e,rr=d===2?5:d===3?(e===1?6:7):8,rec=stats[key]??(stats[key]={subspaces:0,codeCount:0,checked:0,rankPass:0,found:0});rec.subspaces++;
let fs=Array.from({length:16},(_,i)=>i).filter(i=>(s>>i)&1);
// All cases have a full-rank slice supported by exactly 4 terms:
// for d<=3 this follows from the rank-weight sum. For d=4,
// the 3 low-rank slices require >=6 total weight, leaving <=58
// over 12 full-rank slices; some has weight 4.
// Unit transitivity lets us normalize that slice to the fixed pivot 4.
for(let pivot of (d===4?[4]:fs.filter(x=>x>=4))){let bas=[pivot];for(let x of fs)if(!span(bas).includes(x))bas.push(x);let req=Array.from({length:1<<d},(_,i)=>ranks[raw[span(bas)[i]]]);let inv=0;for(let j=0;j<4;j++){let x=0;while(app(raw[pivot],x)!==1<<j)x++;inv|=x<<(4*j)}
let M=bas.map(x=>compose(inv,raw[x]));assert.equal(M[0],0x8421);
let codes=[];function go(i,left,a,w){if(!left){if(w.every((v,k)=>v>=req[k+1])&&w[0]===4)codes.push(a);return}if(i===(1<<d))return;for(let n=0;n<=left;n++){let t=w.map((v,k)=>v+n*parity((k+1)&i));if(t[0]>4||t.some((v,k)=>v+left-n<req[k+1]))continue;go(i+1,left-n,a.concat(Array(n).fill(i)),t)}}go(1,rr,[],Array((1<<d)-1).fill(0));rec.codeCount+=codes.length;
for(let code of codes){let inside=code.filter(x=>x&1),out=code.filter(x=>!(x&1)),nn=out.length;
let mask=(v,x)=>v.reduce((a,c,j)=>a|(parity((c>>1)&x)<<j),0);
let comb=Array.from({length:1<<(d-1)},(_,x)=>mask(out,x)),masks=Array.from({length:1<<(d-1)},(_,x)=>mask(inside,x)),rhs=Array.from({length:1<<(d-1)},(_,x)=>M.slice(1).reduce((z,m,i)=>z^((x>>i&1)?m:0),0)),ws=comb.map(pop);
for(let B of bases){rec.checked++;let v=[0],ok=true;for(let x=1;x<(1<<(d-1));x++){let z=rhs[x];for(let i=0;i<4;i++)if(masks[x]>>i&1)z^=B[i];v[x]=z;if(ranks[z]>ws[x]||(ws[x]===1&&ranks[z]!==1)){ok=false;break}}
if(!ok)continue;rec.rankPass++;
let eq=Array.from({length:d-1},(_,j)=>({mask:comb[1<<j],z:v[1<<j]})),piv=[];
for(let i=0;i<nn;i++){let j=eq.findIndex((a,j)=>j>=piv.length&&(a.mask>>i&1));if(j<0)continue;let k=piv.length;[eq[k],eq[j]]=[eq[j],eq[k]];for(let j=0;j<d-1;j++)if(j!==k&&(eq[j].mask>>i&1)){eq[j].mask^=eq[k].mask;eq[j].z^=eq[k].z}piv.push(i)}
if(eq.some(e=>!e.mask&&e.z))continue;
let free=Array.from({length:nn},(_,i)=>i).filter(i=>!piv.includes(i)),ans=Array(nn).fill(0);
function test(j){if(j<free.length){for(let r of R){ans[free[j]]=r;if(test(j+1))return true}return false}for(let k=0;k<piv.length;k++){let z=eq[k].z;for(let i of free)if(eq[k].mask>>i&1)z^=ans[i];if(ranks[z]!==1)return false;ans[piv[k]]=z}return true}
if(test(0))rec.found++;
}}}}
console.log(JSON.stringify(stats,null,2));
assert.deepEqual(Object.values(stats).map(x=>x.found),[0,0,0,0]);
assert.equal(Object.values(stats).reduce((a,b)=>a+b.checked,0),14575680);
