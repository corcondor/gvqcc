
function windowTensor(lib,d,k){
let b=d.P[k].window,i=0,masks=[];while(b[i]!==3){let t=b[i];if(t===0)i+=36;else if(t===1){masks.push((b[i+1]|b[i+2]<<8|b[i+3]<<16|b[i+4]<<24)>>>0);i+=39}else i+=42+2*(b[i+40]|b[i+41]<<8)}
let q=[...lib.A,...d.rows[k-1],...Array(82).fill(0n)],out=[],idx=0,cache=[];
function low(x){return Number((x&255n)^((x&1n)?255n:0n))>>1}
function high(x){return lib.pack(h=>x>>BigInt(8*h)&1n,153)}
for(let [t,a,b,c] of d.opMap[k]){if(t==="CCX"){let u=q[a],v=q[b];if(c<46)out.push({u:low(u),v:low(v),hu:high(u),hv:high(v),m:masks[idx++]});else cache.push({u,v,g:u&v});q[c]^=u&v}else if(t==="CX")q[b]^=q[a];else if(t==="X")q[a]^=lib.FULL;else if(t==="HMR")q[a]=0n}
let W=lib.basis(),C=[],H=[];const prod=(l,m)=>{let v=0n;for(let j=0;j<7;j++)if(l>>j&1)v|=BigInt(m)<<BigInt(j*30);return v};
for(let p of out){for(let [l,h] of [[p.u,p.hv],[p.v,p.hu]]){let v=prod(l,p.m);if(!W.add(v,lib.qmask(C.length)))throw Error("dependent original");C.push(v);H.push(h)}}
let piv=[...W.p.entries()].sort((a,b)=>b[0]-a[0]).map(([i,[v,c]])=>[lib.qmask(i),v]),qred=v=>{for(let [m,x] of piv)if(v&m)v^=x;return v};
let rel0=Array.from({length:7},(_,j)=>Array.from({length:30},(_,o)=>qred(lib.qmask(j*30+o))));
let Q=Array.from({length:128},(_,l)=>Array.from({length:30},(_,o)=>{let v=0n;for(let j=0;j<7;j++)if(l>>j&1)v^=rel0[j][o];return v}));
let hc=lib.basis(),nulls=[];for(let i=0;i<H.length;i++){let [r,c]=hc.red(H[i],lib.qmask(i));if(r)hc.add(r,c);else nulls.push(c)}
return {out,cache,W,C,H,hc,nulls,prod,Q}
}
function paired(lib,t){
const {Q,W,prod}=t;let cand=[],hist={};
for(let l=1;l<128;l++)for(let m=l+1;m<128;m++){if((l^m)<m)continue;let b=lib.basis(),ns=[];for(let j=0;j<30;j++){let [r,c]=b.red(Q[l][j]|(Q[m][j]<<210n),lib.qmask(j));if(r)b.add(r,c);else ns.push(c)}if(ns.length){hist[ns.length]=(hist[ns.length]??0)+1;if(ns.length>20)throw Error("too large");for(let z=1;z<1<<ns.length;z++){let s=0n;for(let j=0;j<ns.length;j++)if(z>>j&1)s^=ns[j];cand.push({l,m,s:Number(s),c1:W.expr(prod(l,s)),c2:W.expr(prod(m,s))})}}}
return {cand,hist}
}
return {windowTensor,paired}
