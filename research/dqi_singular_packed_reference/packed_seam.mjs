// Exact local GF4096 polynomial encoding audit. No native KMB or score claim.
const exp=new Uint16Array(8190),log=new Int16Array(4096).fill(-1);
let x=1;for(let i=0;i<4095;i++){if(log[x]>=0)throw Error("field cycle");exp[i]=exp[i+4095]=x;log[x]=i;x<<=1;if(x&4096)x^=0x1053}
if(x!==1)throw Error("field cycle");
const m=(a,b)=>a&&b?exp[log[a]+log[b]]:0,inv=a=>{if(!a)throw Error("zero");return exp[4095-log[a]]};
let seed=0x313a27;function rng(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0}const f=()=>rng()&4095;
function add(a,b){const c=new Uint16Array(Math.max(a.length,b.length));for(let i=0;i<c.length;i++)c[i]=(a[i]||0)^(b[i]||0);return c}
function prod(a,b){const c=new Uint16Array(a.length+b.length-1);for(let i=0;i<a.length;i++)for(let j=0;j<b.length;j++)c[i+j]^=m(a[i],b[j]);return c}
function divq(a,k){const r=Uint16Array.from(a),q=new Uint16Array(Math.max(0,a.length-2));for(let j=a.length-1;j>=2;j--){let v=r[j];q[j-2]=v;r[j]=0;r[j-1]^=v;r[j-2]^=m(v,k)}return {q,r:[r[0]||0,r[1]||0]}}
function mul2(a,b,k){let z=m(a[1],b[1]);return [m(a[0],b[0])^m(k,z),m(a[0],b[1])^m(a[1],b[0])^z]}
function inv2(a,k){let [u,v]=a,n=m(u,u)^m(u,v)^m(k,m(v,v)),h=inv(n);return [m(u^v,h),m(v,h)]}
const equal=(a,b)=>{for(let i=0;i<Math.max(a.length,b.length);i++)if((a[i]||0)!==(b[i]||0))return false;return true};
let checks=0,singular=0,collisions=0;
for(let r=2;r<=34;r++)for(let k0=0;k0<34;k0++){
 const a=2*k0,k=2048^m(a,a)^a,Q=[k,1,1];
 for(let j=0;j<24;j++){
 let D=j%3===0?prod(Q,Array.from({length:r-1},f)):Uint16Array.from({length:r+1},f),N=Uint16Array.from({length:r},f),P=[f(),f()];if(!P[0]&&!P[1])P[0]=1;
 let d=divq(D,k).r,g=Number(!d[0]&&!d[1]);if(g)singular++;
 const R=add(prod(Q,N),prod(P,D)),enc=g?add(R,P):R,dr=[d[0]^g,d[1]],p2=mul2(divq(enc,k).r,inv2(dr,k),k);
 const math=g?add(enc,p2):enc,ndiv=divq(add(math,prod(p2,D)),k);
 if(!equal(p2,P)||!equal(ndiv.q,N)||ndiv.r.some(x=>x)||!equal(math,R))throw Error("packed");
 if(g){const d0=divq(D,k).q;const n2=add(N,prod(P,d0));if(!equal(add(prod(Q,n2),prod([0,0],D)),R))throw Error("collision");collisions++}
 checks++;
 }}
console.log(JSON.stringify({checks,singular,explicitUnencodedCollisions:collisions,mismatches:0,scope:"word-level reversible encoding; not a complete physical decoder"}));
