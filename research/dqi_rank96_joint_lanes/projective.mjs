import fs from 'node:fs';
function projectiveAudit(T,other,mod){
 const at=(x,i)=>(x>>>(2*i))&3, iv=[0,1,3,2], sm=(x,y)=>[0,x,((x&2)>>1)^((x&1)<<1)^(x&2),x^(((x&2)>>1)^((x&1)<<1)^(x&2))][y];
 const scale=(v,k)=>{if(!k)return 0;if(k===1)return v;let w=((v&0xaaaaaa)>>>1)^((v&0x555555)<<1)^(v&0xaaaaaa);return k===2?w:w^v};
 const norm=v=>v?scale(v,iv[(v>>>((31-Math.clz32(v&-v))&~1))&3]):0;
 const lo=( (1n<<156n)-1n)/3n, hi=lo<<1n;
 const bs=(v,k)=>{if(k===0)return 0n;if(k===1)return v;let w=((v&hi)>>1n)^((v&lo)<<1n)^(v&hi);return k===2?w:w^v};
 function mat(x){let z=0n,s=0n;for(let i=0;i<12;i++){z|=BigInt(scale(x>>>(2*i),at(x,i)))<<s;s+=BigInt(2*(12-i))}return z}
 const positions=Array.from({length:78},(_,i)=>BigInt(2*i));let rows=[];const originals=T.map(([x,y,w])=>{if(x!==y)throw Error("symmetric");let v=norm(x);return [v,scale(w,sm(at(x,(31-Math.clz32(x&-x))>>1),at(x,(31-Math.clz32(x&-x))>>1)))]});
 const baseTerms=originals.map(([x,w])=>[x,x,w]);
 function reduce(x){let h=0n;for(let r of rows){let k=Number((x>>r[0])&3n);if(k){x^=bs(r[1],k);h^=bs(r[2],k)}}return [x,h]}
 for(let i=0;i<originals.length;i++){let [x,h]=reduce(mat(originals[i][0]));if(!x)throw Error("dependent");let p=BigInt((x.toString(2).length-1)&~1),k=iv[Number((x>>p)&3n)];rows.push([p,bs(x,k),bs(h^(1n<<BigInt(2*i)),k)]);rows.sort((a,b)=>a[0]>b[0]?-1:1)}
 const vec=originals.map(x=>x[0]),V=new Set(vec);
 for(let i=0;i<vec.length;i++)for(let j=i+1;j<vec.length;j++){for(let x=1;x<4;x++)V.add(norm(vec[i]^scale(vec[j],x)));for(let k=j+1;k<vec.length;k++)for(let x=1;x<4;x++)for(let y=1;y<4;y++)V.add(norm(vec[i]^scale(vec[j],x)^scale(vec[k],y)))}
 // Additional isomorphic symmetric dictionaries via 128 invertible field
 // multiplication maps on the input covectors, and every basis Frobenius power.
 const mult=(x,y)=>{let z=0;for(let j=0;j<12;j++){z^=scale(x,at(y,j));let top=x>>>22;x=(x<<2)&0xffffff;if(top)x^=scale(mod,top)}return z};
 let s=0x3274251;const rnd=()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return s&0xffffff};
 function rank(v){let B=new Uint32Array(24),n=0;for(let x of v)while(x){let j=31-Math.clz32(x);if(B[j])x^=B[j];else{B[j]=x;n++;break}}return n}
 let accepted=0;for(let j=0;j<256;j++){let z=rnd();if(!z)continue;let cols=Array.from({length:12},(_,i)=>mult(z,1<<(2*i)));if(rank(cols.flatMap(x=>[x,scale(x,2)]))!==24)continue;accepted++;
 for(let [v] of T.concat(other)){let u=0;for(let i=0;i<12;i++){let t=0;for(let k=0;k<12;k++)t^=sm(at(v,k),at(cols[i],k));u|=t<<(2*i)}V.add(norm(u))}}
 const groups=new Map(),zero=[];let cnt=0;for(let v of V){if(!v||vec.includes(v))continue;let [x,h]=reduce(mat(v));if(!x){zero.push({v,h,s:1});continue}
 let p=BigInt((x.toString(2).length-1)&~1),s=iv[Number(x>>p&3n)],k=bs(x,s),row={v,h:bs(h,s),s};if(groups.has(k))groups.get(k).push(row);else groups.set(k,[row]);cnt++}
 const multi=[...groups.values()].filter(g=>g.length>1),sizes={};for(let g of multi)sizes[g.length]=(sizes[g.length]||0)+1;
 let pairCount=0,tripleCount=0,elims=0,best=baseTerms.length,bestTerms=baseTerms;const old=originals.map(x=>x[1]),coef=(h,i)=>Number(h>>BigInt(2*i)&3n);
 function assess(g,weights){let w=old.slice(),z=[];for(let j=0;j<g.length;j++){let c=weights[j];if(c){for(let i=0;i<w.length;i++)w[i]^=scale(c,coef(g[j].h,i));z.push([g[j].v,g[j].v,scale(c,g[j].s)])}}
 let r=w.filter(Boolean).length+z.length;if(r<best){best=r;bestTerms=w.flatMap((v,i)=>v?[[vec[i],vec[i],v]]:[]).concat(z)}}
 for(let g of zero){for(let i=0;i<old.length;i++){let c=coef(g.h,i);if(c)assess([g],[scale(old[i],iv[c])])}}
 for(let g of multi){for(let i=0;i<g.length;i++)for(let j=i+1;j<g.length;j++){pairCount++;let d=g[i].h^g[j].h;let visited=new Set();for(let k=0;k<old.length;k++){let h=coef(d,k);if(!h)continue;let c=scale(old[k],iv[h]);if(visited.has(c))continue;visited.add(c);assess([g[i],g[j]],[c,c]);elims++}
 for(let l=j+1;l<g.length;l++){tripleCount++;let e=g[i].h^g[l].h,f=g[j].h^g[l].h;let seen=new Set();for(let k=0;k<old.length;k++)for(let m=k+1;m<old.length;m++){let a=coef(e,k),b=coef(f,k),c=coef(e,m),d=coef(f,m),det=sm(a,d)^sm(b,c);if(!det)continue;let x=scale(scale(old[k],d)^scale(old[m],b),iv[det]),y=scale(scale(old[k],c)^scale(old[m],a),iv[det]);let key=x*16777216+y;if(seen.has(key))continue;seen.add(key);assess([g[i],g[j],g[l]],[x,y,x^y]);elims++}}
 }}
 function sig(S){let a=new Uint32Array(144);for(let [x,y,z] of S)for(let i=0;i<12;i++)for(let j=0;j<12;j++)a[12*i+j]^=scale(z,sm(at(x,i),at(y,j)));return a}
 let x=sig(T),y=sig(bestTerms);if(!x.every((v,i)=>v===y[i]))throw Error("coefficient certificate");
 return {seedRank:rows.length,candidates:V.size,isotopies:accepted,zeroCoset:zero.length,nonzeroCosets:groups.size,collisionGroups:multi.length,sizes,pairCount,tripleCount,eliminationTrials:elims,best,bestTerms}
}
const a=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),b=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));const R=[];for(let i=0;i<2;i++)for(let k=0;k<2;k++)R.push({type:i,seed:k,...projectiveAudit((k?b:a)[i].terms,(k?a:b)[i].terms,a[i].mod)});fs.writeFileSync('projective_results.json',JSON.stringify(R,null,2));console.log(R.map(({bestTerms,...r})=>r));
