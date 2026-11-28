// Reconstruct the concrete #314 local quotient from its checked Lean tape.
// Independent enumeration; no general physical full-circuit packing claim.
import fs from 'node:fs';
const src=fs.readFileSync(process.argv[2],'utf8');
const gates=Array.from(src.match(/def second : List G :=\s*\[(.*?)\]/s)[1].matchAll(/\((\d+),(\d+),(\d+),(\d+)\)/g),a=>a.slice(1).map(Number));
function step(x,g){const [o,a,b,t]=g;if(o===49)return x^(((x>>a)&(x>>b)&1)<<t);if(o===33)return x^(((x>>a)&1)<<b);return x^((((x>>a)^(x>>b))&1)*((1<<a)|(1<<b)))}
const pr=x=>(x&1023)|((x>>11)<<10),expand=x=>(x&1023)|((x>>10)<<11);
const out=Array.from({length:8192},(_,i)=>gates.reduce(step,expand(i)));
let valid=[];for(let w=0;w<16384;w++)if(w>>10&1){let v=w,ok=true;for(const g of gates){if(g[0]===49){if((v>>g[1]&1)||(v>>g[2]&1)){ok=false;break}}else v=step(v,g)}if(ok&&(v>>10&1))valid.push([w,v,pr(v)])}
if(valid.length!==128||new Set(out.map(pr)).size!==6144)throw Error('projection census');
const [w,v,d]=valid.find(a=>a[0]===1036);
const seen=new Set();let phaseChecks=0;
for(let i=0;i<8192;i++){
 let x=expand(i),y=x,lam=0,W=w;
 for(const g of gates){
  let z=step(y,g),V=g[0]===49?W:step(W,g);
  // Every gate is equivariant along W; project to a pivot with W[p]=1.
  let p=31-Math.clz32(V&-V),s=(z>>p)&1;
  y=z^(s?V:0);lam^=s;W=V;
 }
 let full=y^(lam?W:0);
 if(full!==out[i])throw Error('equivariance');
 let z=pr(y)^((y>>10&1)?d:0);
 if(z!==(pr(full)^((full>>10&1)?d:0))||seen.has(z))throw Error('encoded collision');
 seen.add(z);
 for(let m=0;m<2;m++){if((m&((y>>10&1)^lam))!==(m&(full>>10&1)))throw Error('phase');phaseChecks++}
}
console.log(JSON.stringify({original_distinct:6144,encoded_distinct:seen.size,valid_directions:valid.length,entry_direction:w,exit_direction:v,projection_xor:d,phase_checks:phaseChecks,scope:'local 13D encoded quotient, not a full 899Q compiler'}));
