// Run: node research/invsqrt36_nonlinear_lending/phase_chart_transport.cjs
function transport(data){
 const fs=data.intervals.map(r=>({id:r.id,vars:r.phase_spectators}));
 function rank(xs){const B=new Map;for(let x of xs){while(x){const k=x.toString(2).length-1;if(B.has(k))x^=B.get(k);else{B.set(k,x);break}}}return B.size}
 const pc=x=>{let n=0;while(x){x&=x-1;n++}return n};
 function phase([a,b,c,d],s){let A=s[a],B=s[b],C=s[c],D=s[d];return A^B^(A&B)^(A&C)^(B&C)^(B&D)^(C&D)}
 let results=[];
 for(let i=0;i<fs.length;i++)for(let j=i+1;j<fs.length;j++){
  const S=fs[i],T=fs[j],U=[...new Set([...S.vars,...T.vars])].sort((a,b)=>a-b),n=U.length,N=1<<n,pivot=14;
  const ds=v=>[[pivot,v[3]],[pivot,v[1],v[2]]];
  for(let di=0;di<2;di++)for(let dj=0;dj<2;dj++){
   const v=ds(S.vars)[di],w=ds(T.vars)[dj];
   const inp=U.map(x=>x===pivot?35:x); const out=Array.from({length:n},()=>Array(N).fill(0));
   for(let x=0;x<N;x++){let y={};inp.forEach((q,k)=>y[q]=x>>k&1);y[pivot]=0;const a=y[35]^phase(S.vars,y);for(const q of v)y[q]^=a;const z=phase(T.vars,y);for(const q of w)y[q]^=a;y[35]=z;inp.forEach((q,k)=>out[k][x]=y[q]);}
   let maxDegree=0,nonlin=[];for(let f of out){for(let k=0;k<n;k++)for(let x=0;x<N;x++)if(x>>k&1)f[x]^=f[x^(1<<k)];let mask=0n;for(let x=0;x<N;x++)if(f[x]){maxDegree=Math.max(maxDegree,pc(x));if(pc(x)>1)mask|=1n<<BigInt(x)}nonlin.push(mask);}
   const r=rank(nonlin),possible=maxDegree<=2&&r<=1;
   results.push({from:S.id,to:T.id,dirFrom:v,dirTo:w,degree:maxDegree,nonlinearRank:r,one_ccx_necessary_test:possible,adjacent:j===i+1});
  }
 }
 return {scope:"Transport between actual phase-derived spectator charts on identical logical states; intervening original instructions NOT included. Degree and nonlinear-output rank are necessary conditions for at most one affine-conjugated CCX; not full KMB proof.",tested:results.length,adjacent:results.filter(r=>r.adjacent).length,eligible:results.filter(r=>r.one_ccx_necessary_test).length,adjacentEligible:results.filter(r=>r.adjacent&&r.one_ccx_necessary_test).length,results};
}
const fs=require('node:fs');
const x=JSON.parse(fs.readFileSync('research/invsqrt36_nonlinear_lending/global_remat/phase_derived_hub_receipt.json','utf8'));
console.log(JSON.stringify(transport(x),null,2));
