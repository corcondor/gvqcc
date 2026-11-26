
function runSpecial(lib,P){
const {bits,bx,features,basis,pack,qmask}=lib;const LOW=[0,1,2,3,4,...Array.from({length:5},(_,i)=>12+i),...Array.from({length:6},(_,i)=>85+i)].reduce((x,i)=>x|qmask(i),0n),HI=[...Array.from({length:7},(_,i)=>5+i),...Array.from({length:68},(_,i)=>17+i)],HIM=HI.reduce((x,i)=>x|qmask(i),0n),MIX=((1n<<99n)-1n)^LOW^HIM;
const bit=(x,i)=>Number(x>>BigInt(i)&1n),par=(x)=>{let s=0;while(x){x&=x-1n;s^=1}return s},pop=x=>bits(x).length;
let F=features(P),n=P.M.length,M=P.M,ord=Array.from({length:16},(_,i)=>i).filter(x=>x!==P.c1&&x!==P.c2),ref=ord[0],slices=[P.c1,P.c2],L=P.U.flatMap((u,i)=>[u,P.V[i]]).map(u=>Number(bx(u&LOW,F)&65535n)),H=P.U.flatMap((u,i)=>[u,P.V[i]]).map(u=>bx(u&HIM,F)),MX=P.U.flatMap((u,i)=>[u,P.V[i]]).map(u=>Number((u&MIX)>>91n));
let constant=L.map(l=>ord.every(x=>((l>>x)&1)===((l>>ref)&1))),freeAll=[];for(let i=0;i<2*n;i++)if(constant[i^1])freeAll.push(i);
let full=[];for(let i=0;i<n;i++)if(constant[2*i]&&constant[2*i+1])full.push(i);
let mixR=Array.from({length:8},(_,i)=>P.R.reduce((s,x,o)=>s|(bit(x,91+i)<<o),0));
let lowR=Array.from({length:16},(_,l)=>P.R.reduce((s,x,o)=>s|(bit(bx(x&LOW,F),l)<<o),0));
let refOld=[],specOld=[],origB=[],hBits=[];
let vals=Array.from({length:77},(_,h)=>Array.from({length:2*n},(_,i)=>bit(H[i],16*h)));
for(let h=0;h<77;h++){let b=0;for(let j=0;j<8;j++)b|=bit(P.B[j],h)<<j;origB.push(b);
 let at=(l,B,drop=-1,change=0,free=[])=>{let r=lowR[l];if(l===P.c1)for(let j=0;j<4;j++)if(B>>j&1)r^=mixR[j];if(l===P.c2)for(let j=4;j<8;j++)if(B>>j&1)r^=mixR[j];
 let d=Array(2*n).fill(0);for(let j=0;j<free.length;j++)if(change>>j&1)d[free[j]]=1;
 let mask=l===P.c1?15:l===P.c2?240:0;
 for(let i=0;i<n;i++)if(i!==drop){let u=((L[2*i]>>l)&1)^vals[h][2*i]^d[2*i]^par(BigInt(MX[2*i]&B&mask)),v=((L[2*i+1]>>l)&1)^vals[h][2*i+1]^d[2*i+1]^par(BigInt(MX[2*i+1]&B&mask));if(u&v)r^=M[i]}return r};
 let r=at(ref,b);refOld.push(r);specOld.push(slices.map(l=>at(l,b)^r));hBits.push(at);
}
// missing high parity constraints using 77 row functions (constant included)
let highFns=[(1n<<77n)-1n,...HI.map(i=>pack(h=>bit(F[i],16*h),77))],lin=basis(),rel=[];
for(let j=0;j<77;j++){let z=highFns.reduce((x,v,i)=>x|BigInt(bit(v,j))<<BigInt(i),0n);let [v,c]=lin.red(z,qmask(j));if(v)lin.add(v,c);else rel.push(c)}
if(rel.length!==1)throw Error("high codim "+rel.length);let parity=rel[0];
function trial(drop,allowMix){
 const free=freeAll.filter(i=>(i>>1)!==drop),opts=[],stats={drop,allowMix,free:free.length,rows:0,choices:0,failed:[]};
 for(let h=0;h<77;h++){
 let at=hBits[h],old=origB[h],r0=at(ref,old,drop),targets=specOld[h],base=[];
 // last high block has only lows 0,1,2, so ignore constraints for absent special lows
 let cared=slices.map(l=>h!==76||l<3);
 for(let b=0;b<256;b++){
  if(!allowMix&&b!==old)continue;
  let delta=slices.map((l,j)=>cared[j]?((at(l,b,drop)^r0)^targets[j]):0),rhs=BigInt(delta[0])|(BigInt(delta[1])<<30n);
  let ds=free.map(i=>{let out=0n;for(let j=0;j<2;j++)if(cared[j]){let l=slices[j],op=i^1,du=((L[op]>>l)^(L[op]>>ref))&1;du^=par(BigInt(MX[op]&b&(j?240:15)));if(du)out|=BigInt(M[i>>1])<<BigInt(30*j)}return out});
  let B=basis(),ker=[];for(let i=0;i<ds.length;i++){let [r,c]=B.red(ds[i],qmask(i));if(r)B.add(r,c);else ker.push(c)}let [r,sol]=B.red(rhs);if(r)continue;
  for(let s=0;s<1<<ker.length;s++){let x=sol;for(let j=0;j<ker.length;j++)if(s>>j&1)x^=ker[j];let u=Number(x);let rr=at(ref,b,drop,u,free)^refOld[h];let z=BigInt(b^old)|(BigInt(u)<<8n)|(BigInt(rr)<<BigInt(8+free.length));
   // verify all available low slices exactly modulo high-only output correction
   if(!Array.from({length:h===76?3:16},(_,l)=>l).every(l=>((at(l,b,drop,u,free)^at(l,old))===rr)))continue;
   base.push({b,u,rr,z});
  }
 }
 if(!base.length){stats.failed.push(h);if(stats.failed.length>2)break}else{stats.rows++;stats.choices+=base.length;opts.push(base)}
 }
 if(stats.failed.length)return {stats};
 // choices to meet missing high parity. Choose baseline nearest, then solve by independent per-row alternatives
 let choose=opts.map((o,h)=>o.slice().sort((a,b)=>pop(a.z)-pop(b.z))[0]);let debt=0n;for(let h=0;h<77;h++)if(bit(parity,h))debt^=choose[h].z;
 if(debt){let B=basis(),alternatives=[];for(let h=0;h<77;h++)if(bit(parity,h)){let o=opts[h];for(let v of o){let z=v.z^choose[h].z;if(z&&B.add(z,qmask(alternatives.length))){alternatives.push([h,v]);break}}}let [r,sol]=B.red(debt);if(r)return {stats:{...stats,parityFailed:true,debt:debt.toString(16),rank:B.p.size}};for(let i of bits(sol)){let [h,v]=alternatives[i];choose[h]=v}}
 let p2={...P,U:P.U.slice(),V:P.V.slice(),M:P.M.slice(),R:P.R.slice(),B:P.B.slice()};
 // encode high coefficient changes in same physical feature basis
 let hb=basis();highFns.forEach((v,i)=>hb.add(v,i===0?1n:qmask(HI[i-1])));
 for(let j=0;j<8;j++)p2.B[j]=pack(h=>choose[h].b>>j&1,77);
 for(let j=0;j<free.length;j++){let delta=pack(h=>choose[h].u>>j&1,77),code=hb.expr(delta);let i=free[j];if(i&1)p2.V[i>>1]^=code;else p2.U[i>>1]^=code}
 for(let j=0;j<30;j++)p2.R[j]^=hb.expr(pack(h=>choose[h].rr>>j&1,77));p2.M[drop]=0;
 let f2=features(p2),d0=P.R.map((r,j)=>bx(r,F)),d1=p2.R.map(r=>bx(r,f2));for(let i=0;i<n;i++){let z=bx(P.U[i],F)&bx(P.V[i],F);for(let j of bits(BigInt(P.M[i])))d0[j]^=z;let z2=bx(p2.U[i],f2)&bx(p2.V[i],f2);for(let j of bits(BigInt(p2.M[i])))d1[j]^=z2}
 if(!d0.every((x,i)=>x===d1[i]))throw Error("special exact mismatch");return {stats:{...stats,pass:true},P:p2};
}
let trials=[];for(let drop of full){for(let allowMix of [false,true]){let t=trial(drop,allowMix);trials.push(t.stats);if(t.P)return {trials,P:t.P,full,freeAll}}}return {trials,full,freeAll}
}
return runSpecial;
