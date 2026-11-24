// Node.js 18+, run from repository root: node research/invsqrt36_nonlinear_lending/phase_derived_hub.cjs
function analyze(lean){
 const assert=(p,m)=>{if(!p)throw Error(m)};
 const lists=new Map([...lean.matchAll(/private def (src|dst)(\d+) : List Gate := \[([\s\S]*?)\]/g)].map(m=>[m[1]+m[2],m[3].trim().split(/,\s*/).map(x=>{const a=x.trim().slice(1).split(/\s+/);return [a[0],...a.slice(1).map(Number)]})]));
 const wires=g=>g[0]==="cx"||g[0]==="ccx"||g[0]==="z"||g[0]==="cz"?g.slice(1):g[0]==="hmr"?[g[1]]:[];
 const paid=g=>g.filter(x=>x[0]==="ccx").length;
 function run(gs,q){
  const p=[0,0];let guard=-1, events=0;
  for(const [op,a,b,c] of gs){
   if(op==="cx")q[b]^=q[a];
   else if(op==="ccx")q[c]^=q[a]&q[b];
   else if(op==="hmr"){if(b<2){p[b]^=q[a];events|=1<<b}q[a]=0;}
   else if(op==="push")guard=a;
   else if(op==="pop")guard=-1;
   else if(op==="z"){if(guard>=0&&guard<2)p[guard]^=q[a]}
   else if(op==="cz"){if(guard>=0&&guard<2)p[guard]^=q[a]&q[b]}
   else if(op!=="clearEvent")throw Error(op)
  }return {p,events};
 }
 const small=Array.from({length:5},(_,i)=>{let m=0;for(let j=0;j<32;j++)if(j>>i&1)m|=1<<j;return m});
 const out=[];
 for(const [key,src] of lists){
  if(!key.startsWith("src"))continue;
  const id=+key.slice(3),dst=lists.get("dst"+id),p=src.findIndex(x=>x[0]==="push");
  if(p<0)continue;
  const end=src.findIndex((x,i)=>i>p&&x[0]==="pop");
  const atoms=src.slice(p+1,end), t=atoms[0][1], b=atoms[1][1], c=atoms[3][2], d=atoms[5][2];
  assert(t===14 && new Set([t,b,c,d]).size===4,"phase structure");
  assert(JSON.stringify(atoms)===JSON.stringify([["z",t],["z",b],["cz",t,b],["cz",t,c],["cz",b,c],["cz",b,d],["cz",c,d]]),"atoms");
  assert(p===7 && src[6][0]==="hmr"&&src[6][1]===35&&src[6][2]===0,"first HMR");
  assert(src.slice(end+1).every(g=>wires(g).every(w=>![t,b,c,d].includes(w))),"spectators changed");
  const first=src[0][2], firstB=src[1][2];
  assert(JSON.stringify(dst.slice(0,3))===JSON.stringify([["cx",first,firstB],["cx",first,35],["ccx",firstB,35,first]]),"MAJ");
  const inv=dst.findIndex((g,i)=>i>3&&JSON.stringify(g)===JSON.stringify(["ccx",firstB,35,first]));
  assert(inv>0&&JSON.stringify(dst.slice(inv,inv+3))===JSON.stringify([["ccx",firstB,35,first],["cx",first,35],["cx",35,firstB]]),"inverse MAJ");
  const rename=(gs,from,to)=>gs.map(g=>[g[0],...g.slice(1).map((x,i)=>wires(g).includes(x)&&x===from&&(g[0]!=="hmr"||i===0)?to:x)]);
  const chart=[["cx",t,d],["cx",35,t],["hmr",t,0],["push",0],["z",b],["cz",b,c],["cz",b,d],["cz",c,d],["pop"],
    ...rename(src.slice(0,6),36,t),...rename(dst.slice(3,inv),first,t),["hmr",t,1],...Array.from({length:6},(_,i)=>["clearEvent",i+2])];
  const decode=[["cx",35,t],["cx",t,35],["cx",d,b],["cx",d,c],["ccx",b,c,t],["cx",d,c],["cx",d,b],["cx",b,t],["cx",d,t],["cx",t,d]];
  assert([...chart,...decode].every(g=>wires(g).every(w=>w<36)),"width");
  const active=[...new Set(src.flatMap(wires))].filter(w=>w!==35&&w!==36).sort((a,b)=>a-b);
  assert(active.length===20,"active vars "+active.length);
  const chunks=2**(active.length-5);
  for(let hi=0;hi<chunks;hi++){
   let q=new Int32Array(37);
   for(let j=0;j<active.length;j++)q[active[j]]=j<5?small[j]:((hi>>(j-5))&1)?-1:0;
   const A=q[t],B=q[b],C=q[c],D=q[d];
   q[35]=A^B^(A&B)^(A&C)^(B&C)^(B&D)^(C&D);
   const qs=q.slice(),qt=q.slice();
   const s=run(src,qs),z=run(chart,qt);
   assert(qt[t]===0&&qt[36]===0&&qt[35]===q[35],"chart boundary");
   const u=qt[d],gg=qt[b]^u^((qt[b]^u)&(qt[c]^u));
   const logical=qt.slice();logical[t]=qt[35]^gg;logical[d]=u^logical[t];logical[35]=0;
   assert(s.events===z.events&&s.p.every((x,i)=>x===z.p[i]),"phase / records "+id+"/"+hi);
   assert(qs.every((x,i)=>x===logical[i]),"open chart mismatch "+id+"/"+hi);
   run(decode,qt);
   assert(qs.every((x,i)=>x===qt[i]),"closing mismatch "+id+"/"+hi);
  }
  out.push({id,phase_spectators:[t,b,c,d],first_carrier:35,new_carrier:t,input_variables:active.length,basis_inputs:2**active.length,arbitrary_events:[0,1],normalized_events:[2,3,4,5,6,7],source_paid:paid(src),pr28_paid:paid(dst),open_paid:paid(chart),close_paid:paid([...chart,...decode]),open_ops:chart.length,close_ops:chart.length+decode.length,chart,decode});
 }
 assert(out.length===10,"ten source intervals");
 return {source_commit:"49263f69b474b686fd92969b03c3374d188ebddd",source_kmb_sha256:"6b59214530108d8c49c648f96c53b963d9b8477f8813db1edcf478bf45f6cf03",scope:"All 2^20 independent active basis assignments per interval, conditional on q35=f(spectators), q36=0. Phase coefficients m0/m1 exact; m2..m7 normalized zero. Unchanged other wires arbitrary by syntactic disjointness. Open chart boundary differs from original ABI. No inter-interval KMB or full oracle.",n:out.length,inputs:out.reduce((n,x)=>n+x.basis_inputs,0),paid:{source:out.reduce((n,x)=>n+x.source_paid,0),pr28:out.reduce((n,x)=>n+x.pr28_paid,0),open:out.reduce((n,x)=>n+x.open_paid,0),closed:out.reduce((n,x)=>n+x.close_paid,0)},intervals:out};
}
const fs=require('node:fs');
const result=analyze(fs.readFileSync('research/invsqrt36_nonlinear_lending/lean/ActualCarry.lean','utf8'));
process.stdout.write(JSON.stringify(result,null,2)+'\n');
