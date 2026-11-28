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
function recover(ts,s){
 const mul=(v,k)=>{if(!k)return 0;if(k===1)return v;let w=((v&0xaaaaaa)>>>1)^((v&0x555555)<<1)^(v&0xaaaaaa);return k===2?w:w^v};
 const sm=(a,b)=>mul(a,b)&3,at=(x,i)=>(x>>>(2*i))&3;
 const parity=x=>{x^=x>>>16;x^=x>>>8;x^=x>>>4;return (0x6996>>>(x&15))&1};
 function inv(cols){let B=new Int32Array(24),C=new Int32Array(24);for(let i=0;i<24;i++){let x=cols[i],c=1<<i;while(x){let p=31-Math.clz32(x);if(!B[p]){B[p]=x;C[p]=c;break}x^=B[p];c^=C[p]}}return x=>{let c=0;while(x){let p=31-Math.clz32(x);if(!B[p])throw Error("rank");x^=B[p];c^=C[p]}return c}}
 const ini=inv(s.inCols),outi=inv(s.outCols),X=Array.from({length:24},(_,i)=>ini(1<<i));
 const target=(ts,x,y)=>{let z=0;for(let [a,b,c] of ts)if(parity(a&x)&&parity(b&y))z^=c;return outi(z)};
 let out=[];
 for(let i=0;i<99;i+=3){let G=ts.slice(i,i+3),found;
  for(let j=0;j<3&&!found;j++)for(let k=0;k<3&&!found;k++){if(j===k)continue;let l=G[j][0],h=G[k][0],v=X.map(x=>parity(l&x)|(parity(h&x)<<1));if(!v.every((x,i)=>i%2===0||x===sm(v[i-1],2)))continue;let form=v.filter((_,i)=>!(i&1)).reduce((a,x,i)=>a|(x<<(2*i)),0);let b0=v.findIndex(x=>x===1);if(b0<0)continue;let w=target(G,X[b0],X[b0]);let ok=true;for(let p=0;p<24&&ok;p++)for(let q=0;q<24;q++){if(target(G,X[p],X[q])!==mul(w,sm(v[p],v[q]))){ok=false;break}}if(ok)found=[form,form,w]}
  if(!found)throw Error("no grouping at "+i);out.push(found)
 }
 function sig(terms){let A=new Uint32Array(144);for(let [a,b,c] of terms)for(let i=0;i<12;i++)for(let j=0;j<12;j++){let v=sm(at(a,i),at(b,j));if(v)A[i*12+j]^=mul(c,v)}return A}
 const x=sig(out),y=sig(s.terms);if(!x.every((v,i)=>v===y[i]))throw Error("seed mismatch");
 return {...s,terms:out};
}
const T=decode(fs.readFileSync(process.argv[2],'utf8')),S=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));const R=[recover(T[0],S[0]),recover(T[2],S[1])];fs.writeFileSync('f16_tower_seeds.json',JSON.stringify(R,null,2));console.log(R.map(s=>s.terms.length));