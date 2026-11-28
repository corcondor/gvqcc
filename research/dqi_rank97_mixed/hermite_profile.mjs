// Exact symmetric profiles for GF(4)[epsilon]/epsilon^2 and a restricted
// degree-12 GF(4) CRT budget screen. Not a global rank lower bound.
import assert from 'node:assert/strict';
const parity=x=>{let p=0;while(x){x&=x-1;p^=1}return p};
const pop=x=>{let p=0;while(x){x&=x-1;p++}return p};
function gf4(a,b){let z=0;while(b){if(b&1)z^=a;b>>=1;a<<=1;if(a&4)a^=7}return z}
function mul(x,y){return gf4(x&3,y&3)|((gf4(x&3,y>>2)^gf4(x>>2,y&3))<<2)}
function matrix(f){let z=0,k=0;for(let i=0;i<4;i++)for(let j=i;j<4;j++,k++)if(parity(f&mul(1<<i,1<<j)))z|=1<<k;return z}
function outer(a){let z=0,k=0;for(let i=0;i<4;i++)for(let j=i;j<4;j++,k++)if((a>>i)&(a>>j)&1)z|=1<<k;return z}
function rank(v){let bas=new Uint16Array(10),n=0;for(let x of v)for(let j=9;j>=0&&x;j--)if(x>>j&1){if(bas[j])x^=bas[j];else{bas[j]=x;n++;break}}return n}
const mats=Array.from({length:16},(_,i)=>matrix(i)),dict=Array.from({length:15},(_,i)=>outer(i+1));
let subs=new Set([1]);for(let i=1;i<16;i++)for(let s of [...subs]){let t=s;for(let j=0;j<16;j++)if(s>>j&1)t|=1<<(j^i);subs.add(t)}
subs=[...subs];assert.equal(subs.length,67);
let best=new Map(subs.map(s=>[s,{cost:Infinity,mask:0}]));
for(let m=0;m<32768;m++){
 let c=pop(m);if(c>9)continue;let B=new Uint16Array(10);
 for(let i=0;i<15;i++)if(m>>i&1){let x=dict[i];for(let j=9;j>=0&&x;j--)if(x>>j&1){if(B[j])x^=B[j];else{B[j]=x;break}}}
 let hit=0;for(let f=0;f<16;f++){let x=mats[f];for(let j=9;j>=0&&x;j--)if(x>>j&1)x^=B[j];if(!x)hit|=1<<f}
 for(let s of subs)if((s&hit)===s&&best.get(s).cost>c)best.set(s,{cost:c,mask:m})
}
let profiles={};
for(let s of subs){let fs=Array.from({length:16},(_,i)=>i).filter(i=>s>>i&1),d=Math.log2(fs.length),e=rank(fs.map(x=>x>>2)),key=d+':'+e,{cost,mask}=best.get(s);if(!profiles[key]||profiles[key].cost>cost)profiles[key]={d,e,cost,s,mask}}
let jets=Object.values(profiles).sort((a,b)=>a.d-b.d||a.e-b.e).map(x=>[x.d,x.e,x.cost]);
assert.deepEqual(jets,[[0,0,0],[1,0,2],[1,1,4],[2,0,3],[2,1,6],[2,2,6],[3,1,7],[3,2,8],[4,2,9]]);
const budget=11,cap=97;
function addPlace(A,degree,d,e){let B=A.slice();for(let k=0;k<=budget;k++){if(k>=degree)B[k]=Math.max(B[k],A[k-degree]+d-e);if(e&&k>=2*degree)B[k]=Math.max(B[k],A[k-2*degree]+d)}return B}
let J=[];function jet(i,left,ls,c,d,A){if(i===jets.length-1){let[x,y,z]=jets[i];for(let n=0;n<left;n++)A=addPlace(A,1,x,y);J.push({c:c+left*z,s:d+left*x,p:A,n:[...ls,left]});return}let[x,y,z]=jets[i];for(let n=0;n<=left;n++){jet(i+1,left-n,[...ls,n],c+n*z,d+n*x,A);A=addPlace(A,1,x,y)}}
jet(0,5,[],0,0,Array(12).fill(0));
function parts(deg,lim,cost){let res=[];function go(k,counts,left,c,s,A){if(k===0){res.push({counts:counts.slice(),c,s,p:A});return}for(let x=0;x<=Math.min(left,Math.floor((cap-c)/cost[k]));x++){counts[k]=x;go(k-1,counts,left-x,c+x*cost[k],s+x*k,A);A=addPlace(A,deg,k,0)}counts[k]=0}go(cost.length-1,Array(cost.length).fill(0),lim,0,0,Array(12).fill(0));return res}
// GF16: 4,6,8,9 (asymmetric partial-3 certificate #320); GF64:
// Griesmer lower bound for partial outputs, exact full rank 15.
let P2=parts(2,6,[0,4,6,8,9]),P3=parts(3,20,[0,6,9,11,12,13,15]);
function merge(A,B){let C=Array(12).fill(0);for(let k=0;k<12;k++)for(let i=0;i<=k;i++)C[k]=Math.max(C[k],A[i]+B[k-i]);return C}
let feasible=0,checked=0,C3=Array.from({length:98},()=>[]);for(let c of P3)for(let j=c.c;j<98;j++)C3[j].push(c);
for(let a of J)for(let b of P2){let cc=a.c+b.c;if(cc>cap)continue;let total=a.s+b.s,A=merge(a.p,b.p);for(let c of C3[cap-cc]){checked++;let dim=total+c.s;if(dim<24||dim-A[11]<24||dim-c.p[11]<24)continue;let loss=0;for(let k=0;k<=11;k++)loss=Math.max(loss,A[k]+c.p[11-k]);if(dim-loss<24)continue;feasible++}}
assert.equal(checked,54997708);assert.equal(feasible,0);
console.log(JSON.stringify({profiles:Object.values(profiles),rationalProfiles:J.length,p2:P2.length,p3:P3.length,checked,feasible},null,2));
