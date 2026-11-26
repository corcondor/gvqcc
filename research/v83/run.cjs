// Reproduce from local fixture JSON and V20 b85 source payload.
const fs = require("fs"), path = require("path");
const load=n=>new Function(fs.readFileSync(path.join(__dirname,n),"utf8"))();
const l=load("angle_core.js"), d=l.inspect(fs.readFileSync(process.argv[2],"utf8"),fs.readFileSync(process.argv[3],"utf8"));
function linearize(l,ops,left,right){
 const N=1219n,F=l.FULL|(l.FULL<<N),join=(a,b)=>a|(b<<N),q=[...l.A.map(v=>join(v,v)),...left.map((v,i)=>join(v,right[i])),...Array(82).fill(0n)];
 let out=[],removed=0,checks=0;
 for(let [t,a,b,c] of ops){
  if(t==="CCX"){let v=q[a]&q[b],B=l.basis();B.add(F,1n);for(let j=0;j<128;j++)if(j!==c&&q[j])B.add(q[j],1n<<BigInt(j+1));let [r,x]=B.red(v);checks++;
   if(!r){if(x&1n)out.push(["X",c]);for(let j of l.bits(x>>1n))out.push(["CX",j,c]);removed++}else out.push([t,a,b,c]);q[c]^=v;
  }else{out.push([t,a,b,c].filter(x=>x!==undefined));if(t==="X")q[a]^=F;else if(t==="CX")q[b]^=q[a];else if(t==="HMR")q[a]=0n}
 }
 return {out,removed,checks};
}
const affine=[];
for(let k=1;k<15;k++){
 let z=linearize(l,d.opMap[k],d.rows[k-1],d.rows[k]),L=l.replay(z.out,d.rows[k-1]),R=l.replay(z.out,d.rows[k]);
 if(!L.words.every((v,i)=>v===d.rows[k][i])||!R.words.every((v,i)=>v===d.rows[k-1][i]))throw Error("replay");
 affine.push({k,checks:z.checks,removed:z.removed});
}
let W=d.W.map((row,adr)=>Array.from({length:75},(_,i)=>{let k=Math.floor(i/5),j=i%5;return d.rows[k].slice(7*j,7*j+7).reduce((s,x,b)=>s|(Number((x>>BigInt(adr))&1n)<<b),0)}));
let C=l.cares(W,d.E),F={};
for(let k=1;k<15;k++){let P=d.P[k];if(!P.window){let f=l.features(P);F[k]=[...f,...P.U.map((u,i)=>l.bx(u,f)&l.bx(P.V[i],f))]}}
let dead=[];
for(let j=0;j<5;j++){let st=[],history=[];for(let k=1;k<15;k++){let V=[...st,...(F[k]||[])],B=l.basis(),out=[];for(let v of V){let [r,c]=B.red(v&C[k*5+j],v);if(r)B.add(r,c);else if(c)out.push(c)}let bb=l.basis();st=out.filter(v=>bb.add(v));history.push(st.length)}dead.push({j,history})}
const wt=load("window_tensor.js"),paired=[];
for(let k of [1,5,7,11]){let t=wt.windowTensor(l,d,k),p=wt.paired(l,t);paired.push({k,W_rank:t.W.p.size,H_rank:t.hc.p.size,paired_candidates:p.cand.length})}
let ss=fs.readFileSync(path.join(__dirname,"special_descent.js"),"utf8").replace("if(stats.failed.length)return {stats};","if(stats.failed.length)return {stats}; return {opts:opts.map(x=>x.map(v=>v.b)),stats};").replace(/let trials=\[\];for\(let drop of full\)[\s\S]*?return runSpecial;/,"return trial(-1,true);\n}\nreturn runSpecial;");
let run=new Function(ss)(),mixed=[];
for(let k=1;k<15;k++){if(d.P[k].window)continue;let r=run(l,d.P[k]),ans=[];if(r.opts)for(let shift of [0,4])for(let m=1;m<16;m++)for(let c of [0,1]){let par=x=>l.bits(BigInt(x)).length%2;if(r.opts.slice(0,76).every(o=>o.some(b=>par((b>>shift)&m)===c)))ans.push({shift,m,c})}mixed.push({k,stats:r.stats,answers:ans})}
console.log(JSON.stringify({baseline:d.stats,affine,dead,paired,mixed,accepted:false},null,2));
