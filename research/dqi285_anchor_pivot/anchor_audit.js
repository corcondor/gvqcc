// Independent GF4096 word reference, not a native circuit or a #285 fixture replay.
function anchorAudit(){
 const exp=new Uint16Array(8190),log=new Uint16Array(4096);let x=1;
 for(let i=0;i<4095;i++){exp[i]=exp[i+4095]=x;log[x]=i;x<<=1;if(x&4096)x^=0x1053}
 const assert=(v,s)=>{if(!v)throw Error(s)};
 assert(x===1,"field generator");
 const m=(a,b)=>a&&b?exp[log[a]+log[b]]:0;
 const inv=a=>{assert(a!==0,"zero inverse");return exp[4095-log[a]]};
 const div=(a,b)=>m(a,inv(b)),sqrt=a=>a?exp[(log[a]*2048)%4095]:0;
 const tr=a=>{let z=0;for(let i=0;i<12;i++){z^=a;a=m(a,a)}return z};
 let seed=285202611;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0}
 const R=()=>rand()&4095,nonzero=()=>1+rand()%4095;
 const trim=a=>{a=a.slice();while(a.length>1&&!a[a.length-1])a.pop();return a};
 const add=(a,b)=>trim(Array.from({length:Math.max(a.length,b.length)},(_,i)=>(a[i]||0)^(b[i]||0)));
 const sc=(a,b)=>trim(a.map(x=>m(x,b)));
 const mul=(a,b)=>{let c=Array(a.length+b.length-1).fill(0);for(let i=0;i<a.length;i++)for(let j=0;j<b.length;j++)c[i+j]^=m(a[i],b[j]);return trim(c)};
 const ev=(a,t)=>{let z=0;for(let i=a.length-1;i>=0;i--)z=m(z,t)^a[i];return z};
 const deriv=a=>trim(a.length===1?[0]:a.slice(1).map((x,i)=>i%2?0:x));
 const eq=(a,b)=>{a=trim(a);b=trim(b);return a.length===b.length&&a.every((x,i)=>x===b[i])};
 const dd=(a,t)=>{if(a.length===1)return [0];let q=Array(a.length-1).fill(0);q[q.length-1]=a[a.length-1];for(let i=q.length-2;i>=0;i--)q[i]=a[i+1]^m(t,q[i+1]);return trim(q)};
 const exact=(a,t)=>{assert(ev(a,t)===0,"not divisible by node");return dd(a,t)};
 const pdiv=(a,b)=>{a=trim(a);b=trim(b);assert(b.some(Boolean),"zero polynomial divisor");let q=Array(Math.max(1,a.length-b.length+1)).fill(0);while(a.some(Boolean)&&a.length>=b.length){let j=a.length-b.length,k=div(a[a.length-1],b[b.length-1]);q[j]^=k;for(let i=0;i<b.length;i++)a[i+j]^=m(k,b[i]);a=trim(a)}return [trim(q),a]};
 const dot=(a,b)=>a.reduce((z,x,i)=>z^m(x,b[i]),0);
 const bracket=(a,b,g)=>add(sc(a,g[1]),sc(b,g[0]));
 const bez=(a,b,t,s)=>t===s?(m(ev(deriv(a),t),ev(b,t))^m(ev(deriv(b),t),ev(a,t))):div(m(ev(a,t),ev(b,s))^m(ev(b,t),ev(a,s)),t^s);
 const totals={cases:0,rhs:0,scalar:0,nonfirst_scalar:0,pair:0,anchor_zero:0,orientation_B_zero:0,schur_entries:0,restored_steps:0,roots:0,phase_checks:0,fixed_order_obstruction_cases:0,nonfirst_cases:0,pair_cases:0,errors:0,weight_counts:{}};
 let current;
 function solve(a,b,ts,rhs){
   let n=ts.length;if(n===0)return rhs.map(()=>[]);
   assert(Math.max(a.length,b.length)===n+1,"degree");
   const K=ts.map(t=>ts.map(s=>bez(a,b,t,s)));
   let pp=[0],mode="scalar";
   if(!K[0][0]){
     current.obstruction=true;totals.anchor_zero++;
     const j=K[0].findIndex((x,i)=>i>0&&x!==0);assert(j>0,"singular anchor");
     if(K[j][j]){pp=[j];totals.nonfirst_scalar++;current.nonfirst=true}
     else{pp=[0,j];mode="pair";totals.pair++;current.pair=true}
   }
   if(mode==="scalar")totals.scalar++;
   const rr=ts.map((_,i)=>i).filter(i=>!pp.includes(i)),ps=pp.map(i=>ts[i]),rs=rr.map(i=>ts[i]);
   const gs=ps.map(t=>[ev(a,t),ev(b,t)]);
   assert(gs.every(g=>g[0]||g[1]),"coprime source pair");
   totals.orientation_B_zero+=gs.filter(g=>!g[1]).length;
   const ws=gs.map((g,i)=>exact(bracket(a,b,g),ps[i]));
   const k=mode==="scalar"?K[pp[0]][pp[0]]:K[pp[0]][pp[1]];
   const ks=v=>mode==="scalar"?[div(v[0],k)]:[div(v[1],k),div(v[0],k)];
   const coeff=mode==="scalar"?[sc(ws[0],inv(k))]:[sc(ws[1],inv(k)),sc(ws[0],inv(k))];
   let a1=a,b1=b;for(let j=0;j<pp.length;j++){a1=add(a1,sc(coeff[j],gs[j][0]));b1=add(b1,sc(coeff[j],gs[j][1]))}
   for(const t of ps){a1=exact(a1,t);b1=exact(b1,t)}
   const H=ps.reduce((p,t)=>mul(p,[t,1]),[1]);
   const hs=rs.map(t=>ev(H,t));
   for(let i=0;i<rr.length;i++)for(let j=0;j<rr.length;j++){
     const row=pp.map(p=>K[rr[i]][p]),col=pp.map(p=>K[p][rr[j]]);
     const want=K[rr[i]][rr[j]]^dot(row,ks(col));
     assert(want===m(m(hs[i],hs[j]),bez(a1,b1,rs[i],rs[j])),"Schur identity");
     totals.schur_entries++;
   }
   if(pp.length===1&&pp[0]!==0)assert(bez(a1,b1,ts[0],ts[0])!==0,"forced next scalar");
   // Restore only from reduced polynomial pair, retained source pairs and node indices.
   let aa=mul(H,a1),bb=mul(H,b1),co;
   if(mode==="scalar"){
     const w=bracket(a1,b1,gs[0]),h=ev(w,ps[0]);assert(h===k,"recovered scalar");
     co=[sc(w,inv(h))];
   }else{
     const recK=div(m(gs[0][0],gs[1][1])^m(gs[0][1],gs[1][0]),ps[0]^ps[1]);assert(recK===k,"recovered pair");
     const u0=mul([ps[0],1],bracket(a1,b1,gs[0])),u1=mul([ps[1],1],bracket(a1,b1,gs[1]));
     co=[sc(u1,inv(recK)),sc(u0,inv(recK))];
   }
   for(let j=0;j<pp.length;j++){aa=add(aa,sc(co[j],gs[j][0]));bb=add(bb,sc(co[j],gs[j][1]))}
   assert(eq(a,aa)&&eq(b,bb),"packed source restore");totals.restored_steps++;
   const child=rhs.map(y=>{const u=ks(pp.map(p=>y[p]));return rr.map((i,j)=>div(y[i]^dot(pp.map(p=>K[i][p]),u),hs[j]))});
   const ys=solve(a1,b1,rs,child);
   return ys.map((y,h)=>{const v=Array(n).fill(0);rr.forEach((i,j)=>v[i]=div(y[j],hs[j]));
     const u=ks(pp.map(p=>rhs[h][p]^dot(rr.map(i=>K[p][i]),rr.map(i=>v[i]))));
     pp.forEach((p,i)=>v[p]=u[i]);
     assert(K.every((row,i)=>dot(row,v)===rhs[h][i]),"RHS solution");
     return v;
   });
 }
 function check(a,b,ts,rs){
   current={obstruction:false,nonfirst:false,pair:false};
   const xs=solve(a,b,ts,rs);
   totals.cases++;totals.rhs+=rs.length;
   totals.fixed_order_obstruction_cases+=+current.obstruction;
   totals.nonfirst_cases+=+current.nonfirst;totals.pair_cases+=+current.pair;
   return xs;
 }
 // Every supported weight; roots, amplitudes and squarefree padding generated independently.
 const pool=Array.from({length:4096},(_,i)=>i).filter(x=>tr(x)===1);
 const sq=a=>{let z=Array(2*a.length-1).fill(0);a.forEach((x,i)=>z[2*i]=m(x,x));return trim(z)};
 for(let w=0;w<=35;w++)for(let rep=0;rep<4;rep++){
   const roots=[];while(roots.length<w){let t=nonzero();if(!roots.includes(t))roots.push(t)}
   const vals=roots.map(nonzero),pads=[];while(pads.length<Math.floor((35-w)/2)){let c=pool[rand()%pool.length];if(!pads.includes(c))pads.push(c)}
   let D=[1];for(const t of roots)D=mul(D,[t,1]);if(w%2===0)D=mul(D,[0,1]);for(const c of pads)D=mul(D,[c,1,1]);assert(D.length===36,"pad degree");
   let N=[0];roots.forEach((t,i)=>N=add(N,sc(exact(D,t),m(vals[i],t))));
   const half=(p,j)=>trim(Array.from({length:Math.max(1,Math.ceil((p.length-j)/2))},(_,i)=>sqrt(p[2*i+j]||0)));
   const A=half(D,0),B=half(D,1),P=half(N,0),Q=half(N,1);
   assert(B.length===18&&eq(D,add(sq(A),mul([0,1],sq(B)))),"half locator");
   const ts=Array.from({length:17},(_,i)=>i);
   const [u,v]=check(A,B,ts,[P,Q].map(f=>{let r=pdiv(f,B)[1];return ts.map(t=>ev(r,t))}));
   const reconstruct=z=>ts.reduce((p,t,i)=>add(p,sc(dd(B,t),z[i])),[0]);
   const U=reconstruct(u),T=reconstruct(v);
   const [Z,remZ]=pdiv(add(P,mul(A,U)),B),[W,remW]=pdiv(add(Q,mul(A,T)),B);
   assert(eq(remZ,[0])&&eq(remW,[0]),"modular inverse");
   const V=add(sq(add(Z,mul([0,1],T))),mul([0,1],sq(add(W,U))));
   assert(eq(mul(sq(B),V),add(N,mul(D,add(sq(U),mul([0,1],sq(T)))))),"magnitude identity");
   let p1=0,p2=0;
   roots.forEach((t,i)=>{let value=div(ev(V,t),t),mask=R();assert(value===vals[i],"physical magnitude");totals.roots++;p1^=tr(m(mask,vals[i]));p2^=tr(m(mask,value))});
   assert(p1===p2,"phase");totals.phase_checks++;
   totals.weight_counts[w]=(totals.weight_counts[w]||0)+1;
 }
 // Force zero diagonals, later nonfirst pivots, local alternating pairs in globally nonalternating matrices.
 for(let n=2;n<=17;n++)for(let rep=0;rep<8;rep++){
   let b=Array.from({length:n+1},R);b[0]=0;b[1]=0;b[n]=nonzero();
   if(rep%2===0&&n>=3){let odd=0;for(let j=5;j<=n;j+=2)odd^=b[j];if(n===3)b[3]=0;else b[3]=odd;if(n===3){b[3]=nonzero();b[1]=0}}
   // Choose a guaranteed nonzero offdiagonal at nodes 0 and 1.
   if(!ev(b,1))b[2]^=1;
   if(!b[n])b[n]=1;
   const ts=Array.from({length:n},(_,i)=>i);
   check([1],trim(b),ts,[ts.map(R),ts.map(R)]);
 }
 return totals;
}
console.log(JSON.stringify(anchorAudit(), null, 2));
