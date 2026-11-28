import fs from 'node:fs';
function decode(s){
 const alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";let data=[],acc=0,bits=0;for(const ch of s.replace(/\s/g,"")){if(ch==="=")break;acc=(acc<<6)|alphabet.indexOf(ch);bits+=6;if(bits>=8){bits-=8;data.push(acc>>bits&255)}}
 let off=2,bit=0;const read=n=>{let v=0;for(let j=0;j<n;j++){v|=((data[off]>>bit)&1)<<j;if(++bit===8){bit=0;off++}}return v};
 function huff(lengths){let c=new Uint32Array(16),next=new Uint32Array(16),maps=Array.from({length:16},()=>new Map());for(let n of lengths)if(n)c[n]++;let code=0;for(let i=1;i<16;i++){code=(code+c[i-1])*2;next[i]=code}for(let i=0;i<lengths.length;i++){let n=lengths[i];if(n)maps[n].set(next[n]++,i)}return maps}
 function sym(tree){let code=0;for(let n=1;n<16;n++){code=(code<<1)|read(1);if(tree[n].has(code))return tree[n].get(code)}throw Error("invalid huffman")}
 const lb=[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258],le=[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0],db=[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577],de=[0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13];
 let out=[],last=0;while(!last){last=read(1);let type=read(2);if(type===0){if(bit){off++;bit=0}let n=read(16);if((read(16)^65535)!==n)throw Error("stored");while(n--)out.push(read(8));continue}let L,D;if(type===1){L=huff(Array.from({length:288},(_,i)=>i<144?8:i<256?9:i<280?7:8));D=huff(Array(32).fill(5))}else if(type===2){let nl=read(5)+257,nd=read(5)+1,nc=read(4)+4;let order=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15],cl=Array(19).fill(0);for(let i=0;i<nc;i++)cl[order[i]]=read(3);let ct=huff(cl),lens=[];while(lens.length<nl+nd){let a=sym(ct);if(a<16)lens.push(a);else{let n=a===16?read(2)+3:a===17?read(3)+3:read(7)+11,v=a===16?lens[lens.length-1]:0;while(n--)lens.push(v)}}L=huff(lens.slice(0,nl));D=huff(lens.slice(nl))}else throw Error("type");while(true){let a=sym(L);if(a<256){out.push(a);continue}if(a===256)break;a-=257;let n=lb[a]+read(le[a]),d=sym(D),dist=db[d]+read(de[d]);while(n--)out.push(out[out.length-dist])}}
 if(out.length!==3564)throw Error(out.length);let nums=[];for(let i=0;i<out.length;i+=3)nums.push(out[i]|out[i+1]<<8|out[i+2]<<16);let T=[];for(let i=0;i<nums.length;i+=297){let ts=[];for(let j=i;j<i+297;j+=3)ts.push(nums.slice(j,j+3));T.push(ts)}return T
}
function construct(ts){
 const parity=x=>{x^=x>>>16;x^=x>>>8;x^=x>>>4;return (0x6996>>>(x&15))&1};
 const mul0=(x,y)=>{let z=0;for(const [a,b,w] of ts)if(parity(a&x)&&parity(b&y))z^=w;return z};
 function makeBasis(vs){let B=new Int32Array(24),C=new Int32Array(24),r=0;for(let v of vs){let x=v,c=1<<r;while(x){let i=31-Math.clz32(x);if(!B[i]){B[i]=x;C[i]=c;r++;break}x^=B[i];c^=C[i]}}return {rank:r,coord(v){let c=0;while(v){let i=31-Math.clz32(v);if(!B[i])return -1;v^=B[i];c^=C[i]}return c}}}
 let unit=0,iso;
 for(let i=0;i<24;i++){const f=makeBasis(Array.from({length:24},(_,j)=>mul0(1<<i,1<<j)));if(f.rank===24){unit=1<<i;iso=f;break}}
 if(!unit)throw Error("no unit");
 const mul=(x,y)=>iso.coord(mul0(x,y));function pow(x,n){let z=unit;while(n){if(n&1)z=mul(z,x);x=mul(x,x);n>>>=1}return z}
 let r=0x9e3779b9;const rnd=()=>{r^=r<<13;r^=r>>>17;r^=r<<5;return r&0xffffff};
 let beta=0,theta=0,bas,coords;for(let i=0;i<200;i++){let v=pow(rnd(),(16777215/3)|0);v=mul(v,v);if((mul(v,v)^v^unit)===0){beta=v;break}}
 if(!beta)throw Error("GF4");
 const F=(a,x)=>((a&1)?x:0)^((a&2)?mul(beta,x):0);
 for(let k=0;k<500;k++){let v=rnd(),u=unit,bs=[];for(let i=0;i<12;i++){bs.push(u,mul(beta,u));u=mul(u,v)}let co=makeBasis(bs);if(co.rank===24){theta=v;bas=bs;coords=co;break}}
 if(!theta)throw Error("generator");
 const mod=coords.coord(pow(theta,12));
 const m4=(a,b)=>{let x=0;while(b){if(b&1)x^=a;b>>=1;a<<=1;if(a&4)a^=7}return x};
 const s4=(v,c)=>{let x=0;for(let i=0;i<12;i++)x|=m4((v>>>(2*i))&3,c)<<(2*i);return x};
 const fm=(x,y)=>{let v=0;for(let i=0;i<12;i++){v^=s4(x,(y>>>(2*i))&3);const h=x>>>22;x=(x<<2)&0xffffff;if(h)x^=s4(mod,h)}return v};
 function lin(bits){let z=0;for(let i=0;i<24;i++)if(bits>>i&1)z^=bas[i];return z}
 for(let i=0;i<24;i++)for(let j=0;j<24;j++){if(lin(fm(1<<i,1<<j))!==mul(bas[i],bas[j]))throw Error("isomorphism")}
 const pm=(x,y)=>{let z=Array(x.length+y.length-1).fill(0);for(let i=0;i<x.length;i++)for(let j=0;j<y.length;j++)z[i+j]^=m4(x[i],y[j]);return z};
 const ev=(p,x)=>{let v=0;for(let i=p.length-1;i>=0;i--)v=m4(v,x)^p[i];return v};
 const rem=(p,f)=>{let x=p.slice(),d=f.length-1;for(let j=x.length-1;j>=d;j--){let t=x[j];if(t)for(let k=0;k<=d;k++)x[j-d+k]^=m4(t,f[k])}return Array.from({length:d},(_,i)=>x[i]||0)};
 function invmat(A){let n=A.length,B=A.map((r,i)=>r.concat(Array.from({length:n},(_,j)=>+(i===j))));for(let i=0;i<n;i++){let j=i;while(j<n&&!B[j][i])j++;if(j===n)throw Error("singular");[B[i],B[j]]=[B[j],B[i]];let u=m4(B[i][i],B[i][i]);B[i]=B[i].map(x=>m4(x,u));for(let j=0;j<n;j++)if(j!==i){let u=B[j][i];if(u)B[j]=B[j].map((x,k)=>x^m4(u,B[i][k]))}}return B.map(r=>r.slice(n))}
 const places=[];for(let i=0;i<4;i++)places.push([i,1]);places.push(null);
 for(let d of [2,3]){let count=0;for(let x=0;x<4**d;x++){let f=Array.from({length:d},(_,i)=>(x>>>(2*i))&3).concat([1]);if([0,1,2,3].some(t=>ev(f,t)===0))continue;places.push(f);if(++count===(d===2?6:2))break}}
 const maps=(p,max)=>{let a=[];for(let f of places){if(f===null)a.push(p[max]||0);else a.push(...rem(p,f))}return a};
 const A=Array.from({length:23},(_,i)=>Array.from({length:23},(_,j)=>maps(Array.from({length:23},(_,k)=>+(j===k)),22)[i]));const B=invmat(A);
 const modPoly=Array.from({length:12},(_,i)=>(mod>>>(2*i))&3).concat([1]);
 const R=Array.from({length:23},(_,j)=>rem(B.map(row=>row[j]),modPoly).reduce((v,c,i)=>v|(c<<(2*i)),0));
 const rows=Array.from({length:23},(_,i)=>Array.from({length:12},(_,j)=>maps(Array.from({length:12},(_,k)=>+(j===k)),11)[i]).reduce((v,c,j)=>v|(c<<(2*j)),0));
 let terms=[],pos=0;
 for(let f of places){
  let d=f===null?1:f.length-1;
  if(d===1){terms.push([rows[pos],rows[pos],R[pos]]);pos++;continue}
  const locs=d===2?[0,1,null]:[0,1,2,3,null],n=2*d-1;
  const interp=invmat(locs.map(t=>Array.from({length:n},(_,i)=>t===null?+(i===n-1):ev(Array.from({length:n},(_,j)=>+(i===j)),t))));
  for(let i=0;i<n;i++){let u=0;for(let k=0;k<d;k++){let c=locs[i]===null?+(k===d-1):ev(Array.from({length:d},(_,j)=>+(k===j)),locs[i]);u^=s4(rows[pos+k],c)}
   const w=rem(interp.map(r=>r[i]),f);let z=0;for(let j=0;j<d;j++)z^=s4(R[pos+j],w[j]);terms.push([u,u,z])}
  pos+=d;
 }
 const dot=(u,v)=>{let z=0;for(let j=0;j<12;j++)z^=m4((u>>>(2*j))&3,(v>>>(2*j))&3);return z};
 if(terms.length!==33)throw Error("rank");
 for(let i=0;i<12;i++)for(let j=0;j<12;j++){let x=1<<(2*i),y=1<<(2*j),z=0;for(const [u,v,w] of terms)z^=s4(w,m4(dot(u,x),dot(v,y)));if(z!==fm(x,y))throw Error("CRT")}
 // conversion to normalized original 24-bit x/y masks and output coordinates.
 const inCols=Array.from({length:24},(_,j)=>coords.coord(1<<j));
 const outCols=bas.map(x=>mul0(unit,x));
 return {unit,beta,theta,mod,terms,places,inCols,outCols};
}
const T=decode(fs.readFileSync(process.argv[2],'utf8'));const R=[construct(T[0]),construct(T[2])];fs.writeFileSync('f4_seeds.json',JSON.stringify(R,null,2));console.log(R.map(r=>({rank:r.terms.length,mod:r.mod,unit:r.unit,beta:r.beta,theta:r.theta})))