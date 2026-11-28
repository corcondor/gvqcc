import fs from 'node:fs';
import assert from 'node:assert/strict';
// #314 second, exact pinned Lean gate list; source is independently compared.
const original=[["CCX",0,1,10],["CX",1,0],["SWAP",1,2],["CX",10,1],["SWAP",2,3],["CX",10,2],["SWAP",3,7],["SWAP",7,8],["SWAP",8,12],["SWAP",12,13],["SWAP",13,5],["CX",0,5],["CX",4,5],["CX",5,4],["CX",11,4],["CX",4,11],["CX",6,11],["SWAP",6,9],["CX",11,9],["CX",10,9],["CX",9,10],["CCX",1,2,10],["CX",9,1],["CX",9,2],["CX",10,9],["CX",10,1],["CX",9,10],["CX",9,1],["SWAP",11,6],["SWAP",4,6],["SWAP",5,6],["SWAP",13,6],["SWAP",12,6],["SWAP",8,6],["SWAP",7,6],["SWAP",3,6],["SWAP",2,6],["CX",1,10],["CX",1,9],["SWAP",1,6],["CCX",2,3,10],["CX",10,9],["CX",10,6],["CX",10,2],["CX",10,1],["CX",9,6],["CX",9,4],["CX",9,5],["CX",9,13],["CX",9,3],["CX",9,2],["CX",6,10],["CX",6,8],["CX",6,3],["CX",6,2],["CX",6,1],["CX",6,0],["CX",11,10],["CX",11,1],["CX",11,0],["CX",4,9],["CX",4,6],["CX",4,8],["CX",4,3],["CX",4,0],["CX",5,10],["CX",5,3],["CX",5,2],["CX",5,1],["CX",5,0],["SWAP",5,11],["CX",13,10],["CX",13,9],["CX",13,3],["CX",13,1],["SWAP",13,4],["CX",12,9],["CX",12,3],["CX",8,9],["CX",8,6],["CX",8,3],["CX",8,0],["SWAP",8,11],["CX",7,9],["CX",7,2],["CX",7,0],["SWAP",7,4],["CX",3,0],["SWAP",3,4],["CX",2,10],["CX",2,9],["CX",2,11],["CX",2,1],["SWAP",2,12],["CX",1,10],["CX",1,0],["SWAP",1,6],["CX",0,11],["CX",0,12],["SWAP",0,3]];
const encoded=[["CX",2,3],["CCX",0,1,2],["CX",2,3],["CX",0,1],["CX",0,4],["CX",0,6],["CX",0,10],["CCX",2,3,0],["CX",0,10],["CX",0,6],["CX",0,4],["CX",0,3],["CX",0,4],["CX",0,6],["CX",0,10],["CCX",7,8,0],["CX",0,10],["CX",0,6],["CX",0,4],["CX",0,3],["CX",0,1],["CX",4,3],["CX",4,1],["CX",4,0],["CX",0,11],["CX",0,8],["CX",0,3],["CX",0,2],["CX",11,7],["CX",11,1],["CX",11,0],["CX",6,11],["CX",6,3],["CX",5,11],["CX",5,8],["SWAP",5,11],["CX",8,1],["SWAP",8,4],["CX",12,4],["CX",12,3],["SWAP",12,6],["CX",10,4],["CX",10,2],["SWAP",10,8],["CX",1,7],["CX",1,2],["SWAP",1,6],["CX",7,6],["CX",7,5],["SWAP",7,10],["CX",2,3],["SWAP",2,11],["CX",3,5],["SWAP",3,10],["CX",9,6],["SWAP",9,5]];
const lift=i=>i>=10?i+1:i;
const canonical=[["CX",10,2],["CX",10,3],["CX",0,10],["CX",3,10],...encoded.map(([o,...a])=>[o,...a.map(lift)]),["CX",10,3],["CX",10,6],["CX",10,9],["CX",10,12]];
const bit=(s,i)=>(s>>i)&1;
const expand=x=>(x&1023)|((x>>10)<<11);
const project=x=>(x&1023)|((x>>11)<<10);
function run(s,ops){for(let [o,a,b,t] of ops){if(o==="CCX")s^=(bit(s,a)&bit(s,b))<<t;else if(o==="CX")s^=bit(s,a)<<b;else if(o==="SWAP"){if(bit(s,a)^bit(s,b))s^=(1<<a)|(1<<b)}else throw Error(o)}return s}
function absorb(ops){let p=Array.from({length:14},(_,i)=>i),out=[];for(let [o,...a] of ops){if(o==="SWAP")[p[a[0]],p[a[1]]]=[p[a[1]],p[a[0]]];else out.push([o,...a.map(i=>p[i])])}return {p,ops:out}}
const a=absorb(original),b=absorb(canonical);
for(let i=0;i<14;i++)if(b.p[i]!==a.p[i]){let j=b.p.indexOf(a.p[i]);b.ops.push(["SWAP",b.p[i],b.p[j]]);[b.p[i],b.p[j]]=[b.p[j],b.p[i]]}
const pin=fs.readFileSync(new URL('../dqi_scope_dual_quotient/ScopeDualQuotient.lean',import.meta.url),'utf8');
const pinned=[...pin.match(/def second : List G :=\s*\[(.*?)\]/s)[1].matchAll(/\((\d+),(\d+),(\d+),(\d+)\)/g)].map(x=>x.slice(1).map(Number)).map(([o,a,b,t])=>o===49?["CCX",a,b,t]:[o===33?"CX":"SWAP",a,b]);
assert.deepEqual(original,pinned);
let safe=[],fibre=new Uint8Array(8192),seen=new Set(),images=[new Set(),new Set()],projected=[],ys=[];
for(let w=1;w<16384;w++){
 if(!bit(w,10))continue;let v=w,ok=true;
 for(let g of original){if(g[0]==="CCX"){if(bit(v,g[1])||bit(v,g[2])){ok=false;break}}else v=run(v,[g])}
 if(ok){assert.equal(bit(v,10),1);safe.push([w,v])}
}
assert.equal(safe.length,128);assert(safe.some(([w,v])=>w===1036&&v===5704));
for(let x=0;x<8192;x++){
 let s=run(expand(x),original),h=bit(x,0)^bit(x,3),y=run(x,encoded),z=project(s);
 assert.equal(bit(s,10),h);assert.equal(y,project(s^(h?5704:0)));
 seen.add(y);fibre[z]++;images[h].add(z);projected.push(z);ys.push(y);
 for(let m=0;m<2;m++)assert.equal((m&bit(x,0))^(m&bit(x,3)),m&bit(s,10));
}
assert.equal(seen.size,8192);assert.deepEqual([0,1,2].map(k=>fibre.filter(x=>x===k).length),[2048,4096,2048]);
assert.deepEqual(images.map(x=>x.size),[4096,4096]);
for(let x=0;x<16384;x++){
 assert.equal(run(x,original),run(x,canonical));
 assert.equal(run(x,a.ops),run(x,b.ops));
}
function nonlinRank(values){let c=Uint16Array.from(values);for(let i=0;i<13;i++)for(let s=0;s<8192;s++)if(bit(s,i))c[s]^=c[s^(1<<i)];
 let basis=new Uint16Array(13),n=0;for(let i=1;i<c.length;i++)if(i&(i-1)){let v=c[i];for(let j=12;j>=0;j--)if(bit(v,j)){if(basis[j])v^=basis[j];else{basis[j]=v;n++;break}}}return n}
assert.equal(nonlinRank(projected),3);assert.equal(nonlinRank(ys),3);
const codes={CX:33,SWAP:34,CCX:49};
function array(name,g){return 'const Local '+name+'[] = {\n'+g.map(([o,a,b,t=0])=>'{'+[codes[o],a,b,t].join(',')+'}').join(',\n')+'\n};\n'}
fs.writeFileSync('gate_tables.hpp',array('raw_pattern',original)+array('raw_replacement',canonical)+array('flat_pattern',a.ops)+array('flat_replacement',b.ops));
fs.writeFileSync('gate_tables.json',JSON.stringify({original,encoded,canonical,flat_pattern:a.ops,flat_replacement:b.ops},null,2));
const receipt={safe_directions:128,encoded_states:8192,phase_checks:16384,arbitrary_dirty_unitary_checks:16384,absorbed_unitary_checks:16384,old_ops:original.length,encoded_ops:encoded.length,encoded_phase_ops:encoded.length+2,canonical_ops:canonical.length,flat_old:a.ops.length,flat_new:b.ops.length,ccx:3,canonical_image:6144,nonlinear_output_rank:3};
fs.writeFileSync('local_certificate.json',JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
