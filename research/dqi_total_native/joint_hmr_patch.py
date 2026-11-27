"""Joint arithmetic rebuild of #252: exact tensor HMR, controlled scaling and two-level trace phase.
Run on the unchanged #252 sources before build.py. No input-dependent host decisions."""
from pathlib import Path
p=Path("total.cpp.in");s=p.read_text()
assert "void scaling(int y,int mult,int inverse)" in s
pos=s.index("void maskedmx(")
new=r'''
using Term=array<int,3>;
vector<Term> rank12,rank6,rank3;
constexpr int MB=49140,PB=49152;
void hmr(int q,int b){w.add({80,q,-1,-1,(I)b});}
void clearb(int b){w.add({64,-1,-1,-1,(I)b});}
void bx(int b,int dst){w.add({194,-1,-1,-1,(I)dst,(I)b});}
void czm(int a,int b,int m){w.add({160,a,b,-1,0,(I)m});}
void zm(int a,int m){w.add({144,a,-1,-1,0,(I)m});}
void cxm(int a,int b,int m){w.add({161,a,b,-1,0,(I)m});}
void ccm(int a,int b,int t,int m){w.add({177,a,b,t,0,(I)m});}
int piv(int a,int mask){int q=__builtin_ctz((unsigned)mask);for(int j=q+1;j<12;j++)if(mask>>j&1)w.cx(a+j,a+q);return a+q;}
void unpiv(int a,int mask){int q=__builtin_ctz((unsigned)mask);for(int j=11;j>q;j--)if(mask>>j&1)w.cx(a+j,a+q);}
int phase_mask(int m,int z){
 if(!(z&(z-1)))return m+__builtin_ctz((unsigned)z);
 clearb(PB);for(int i=0;i<12;i++)if(z>>i&1)bx(m+i,PB);return PB;
}
void pay(int a,int b,const vector<Term>& terms,int mask,bool guarded=false){
 for(auto [x,y,z]:terms){int A=piv(a,x),B=piv(b,y),m=phase_mask(mask,z);
  if(!guarded)czm(A,B,m);
  else{
   int d=H;
   ccm(FL,A,d,m);czm(d,B,m);ccm(FL,A,d,m);czm(d,B,m);
  }
  unpiv(b,y);unpiv(a,x);
 }
}
void init_ranks(){
 uint64_t lin[36],nl[36]={};for(int j=0;j<36;j++)lin[j]=uint64_t(1)<<j;
 vector<pair<int,int>> lr;int k=0;
 for(int c:codes){int a=c%64,b=(c/64)%64;
  if(c<4096){lin[b]^=lin[a];nl[b]^=nl[a];}
  else{
   assert(!nl[a]&&!nl[b]);uint64_t x=lin[a],y=lin[b];
   if(x&0xfff000)swap(x,y);
   assert(x&&y&&!(x&~0xfffULL)&&!(y&~0xfff000ULL));
   lr.push_back({(int)x,(int)(y>>12)});nl[c/4096-1]^=uint64_t(1)<<k++;
  }
 }
 assert(k==42);for(int j=0;j<24;j++)assert(nl[j]==0);
 for(int i=0;i<42;i++){int z=0;for(int j=0;j<12;j++)if(nl[24+j]>>i&1)z|=1<<j;assert(z);rank12.push_back({lr[i].first,lr[i].second,z});}
 for(int i=0;i<12;i++)for(int j=0;j<12;j++){int z=0;for(auto [a,b,v]:rank12)if((a>>i&1)&&(b>>j&1))z^=v;assert(z==mul(1<<i,1<<j));}
 rank3={{1,1,7},{2,2,14},{4,4,28},{3,3,2},{5,5,4},{6,6,8}};
 for(auto &t:rank3){int &v=t[2];while(v>=8)v^=0xb<<(31-__builtin_clz((unsigned)v)-3);}
 // Rank-15 GF64 product by degree-2 interpolation over GF4, as in #237.
 auto m=[](int a,int b){return gm(a,b,6,0x43);};
 auto pw=[](int a,int e){return gp(a,e,6,0x43);};
 int w4=0;for(int j=2;j<64;j++)if((m(j,j)^j^1)==0){w4=j;break;}assert(w4);
 int alpha=2;while(alpha==w4||alpha==(w4^1))alpha++;
 int base[]={1,w4,alpha,m(alpha,w4),m(alpha,alpha),m(m(alpha,alpha),w4)},co[64]={};
 set<int> seen;for(int j=0;j<64;j++){int z=0;for(int i=0;i<6;i++)if(j>>i&1)z^=base[i];co[z]=j;seen.insert(z);}assert(seen.size()==64);
 auto ev=[&](int x,int t){int v=co[x],c[3]={};for(int j=0;j<3;j++){if(v>>(2*j)&1)c[j]^=1;if(v>>(2*j+1)&1)c[j]^=w4;}return t<0?c[2]:c[0]^m(c[1],t)^m(c[2],m(t,t));};
 auto sub=[&](int x){assert(x==0||x==1||x==w4||x==(w4^1));return x==0?0:x==1?1:x==w4?2:3;};
 V pts={0,1,w4,w4^1,-1},weights;
 for(int t:pts){int u=1;if(t>=0){for(int z:pts)if(z>=0&&z!=t)u=m(u,m(alpha^z,pw(t^z,62)));}else{u=pw(alpha,4);for(int j=0;j<4;j++)u^=m(pw(pts[j],4),weights[j]);}weights.push_back(u);
  int a=0,b=0;for(int j=0;j<6;j++){int v=sub(ev(1<<j,t));a|=(v&1)<<j;b|=(v>>1)<<j;}
  rank6.push_back({a,a,m(u,1^w4)});rank6.push_back({b,b,u});rank6.push_back({a^b,a^b,m(u,w4)});
 }
 for(int n:{3,6})for(int i=0;i<n;i++)for(int j=0;j<n;j++){int z=0;for(auto [a,b,v]:n==3?rank3:rank6)if((a>>i&1)&&(b>>j&1))z^=v;assert(z==fm(1<<i,1<<j,n));}
}
void product(int a,int b,int t,const vector<Term>& terms){
 for(auto [x,y,z]:terms){int A=piv(a,x),B=piv(b,y),Z=__builtin_ctz((unsigned)z);
  for(int j=Z+1;j<12;j++)if(z>>j&1)w.cx(t+Z,t+j);cc(A,B,t+Z);
  for(int j=11;j>Z;j--)if(z>>j&1)w.cx(t+Z,t+j);unpiv(b,y);unpiv(a,x);
 }
}
void measureword(int q,int n,int b=MB){for(int j=0;j<n;j++)hmr(q+j,b+j);}
void linear_debt(int a,const V& cols,int b){
 for(int j=0;j<int(cols.size());j++)if(cols[j])zm(a+j,phase_mask(b,cols[j]));
}
void norm_prod(int a,int b,int n,int d,int k,const vector<Term>& terms){
 lx(a,n,frobcols(d,2));lx(b,n,frobcols(d,2,k));product(a,b,n,terms);
}
void norm_debt(int a,int b,int d,int k,const vector<Term>& terms,int mask){
 linear_debt(a,frobcols(d,2),mask);linear_debt(b,frobcols(d,2,k),mask);pay(a,b,terms,mask);
}
void maskedmx(int a,int b,int t,int temp){
 assert(a!=b&&a!=t&&b!=t&&temp!=a&&temp!=b&&temp!=t);
 for(int j=0;j<12;j++)cc(FL,a+j,temp+j);
 mx(temp,b,t);measureword(temp,12);
 for(int j=0;j<12;j++)czm(FL,a+j,MB+j);
}
void scaling(int y,int mult,int inverse){
 // T=y*mult; controlled swap. T after swap is y*mult or y*inverse.
 mx(y,mult,T);csword(y,T);measureword(T,12);
 pay(y,mult,rank12,MB);
 xorword(mult,inverse);pay(y,inverse,rank12,MB,true);xorword(mult,inverse);
}
'''
end=s.index("void swap_pivot(",pos)
s=s[:pos]+new+s[end:]
a=s.index("void phase(int count)");b=s.index("int main(",a)
s=s[:a]+r'''
void root_toggle(int f){
 for(int j=0;j<12;j++)w.x(f+j);
 cc(f,f+1,C);for(int j=2;j<11;j++)cc(C+j-2,f+j,C+j-1);cc(C+9,f+11,FL);
 for(int j=10;j>=2;j--){hmr(C+j-1,MB);czm(C+j-2,f+j,MB);}
 hmr(C,MB);czm(f,f+1,MB);
 for(int j=0;j<12;j++)w.x(f+j);
}
int tr(int a,int d){int z=0;for(int j=0;j<d;j++){z^=a;a=fm(a,a,d);}assert(z==0||z==1);return z;}
int dual[12],tow[4096];V tracematrix3;
void init_masks(){
 for(int j=0;j<12;j++){int x=0;for(;x<4096;x++){bool ok=true;for(int i=0;i<12;i++)if(tr(mul(x,1<<i),12)!=(i==j)){ok=false;break;}if(ok)break;}assert(x<4096);dual[j]=x;}
 for(int i=0;i<4096;i++){int z=0;for(int j=0;j<12;j++)if(i>>j&1)z^=basis12[j];tow[z]=i;}
 for(int j=0;j<3;j++){int z=0;for(int k=0;k<3;k++)if(tr(fm(1<<j,1<<k,3),3))z|=1<<k;tracematrix3.push_back(z);}
}
void masked_num(int p,int mask){
 static V cols[12][12];static bool ready=false;
 if(!ready){ready=true;for(int i=0;i<12;i++)for(int j=0;j<12;j++){int z=tow[mul(1<<i,dual[j])];for(int k=0;k<12;k++)if(z>>k&1)cols[i][j].push_back(k);}}
 for(int i=0;i<12;i++)for(int j=0;j<12;j++)for(int k:cols[i][j])cxm(p+i,C+k,mask+j);
}
void inverse3_xor(int a,int h){
 V anf(8);for(int j=0;j<8;j++)anf[j]=gp(j,6,3,0xb);
 for(int k=0;k<3;k++)for(int j=0;j<8;j++)if(j>>k&1)anf[j]^=anf[j^(1<<k)];
 for(int j=1;j<8;j++)if(anf[j]){int z=__builtin_ctz((unsigned)anf[j]);for(int k=z+1;k<3;k++)if(anf[j]>>k&1)w.cx(h+z,h+k);
  V q;for(int k=0;k<3;k++)if(j>>k&1)q.push_back(a+k);
  if(q.size()==1)w.cx(q[0],h+z);else{assert(q.size()==2);cc(q[0],q[1],h+z);}
  for(int k=2;k>z;k--)if(anf[j]>>k&1)w.cx(h+z,h+k);
 }
}
void inverse3_debt(int a,int mask){
 V anf(8);for(int j=0;j<8;j++)anf[j]=gp(j,6,3,0xb);
 for(int k=0;k<3;k++)for(int j=0;j<8;j++)if(j>>k&1)anf[j]^=anf[j^(1<<k)];
 for(int j=1;j<8;j++)if(anf[j]){V q;for(int k=0;k<3;k++)if(j>>k&1)q.push_back(a+k);int m=phase_mask(mask,anf[j]);if(q.size()==1)zm(q[0],m);else{assert(q.size()==2);czm(q[0],q[1],m);}}
}
void trace_kernel(int f,int d,int p,int mask){
 root_toggle(f);
 frame(d,basis12,true);int a=d,b=d+6,u=C,v=C+6,n=T,c=T+6;
 masked_num(p,mask);
 norm_prod(a,b,n,6,kap6,rank6);product(a,v,c,rank6);product(b,u,c,rank6);
 masked_num(p,mask);
 frame(n,basis6,true);frame(c,basis6,true);
 int a0=n,a1=n+3,c0=c,c1=c+3,nn=C,ccross=C+3,h=C+6;
 norm_prod(a0,a1,nn,3,kap3,rank3);product(a0,c1,ccross,rank3);product(a1,c0,ccross,rank3);
 inverse3_xor(nn,h);
 frame(ccross,tracematrix3,false);
 for(int j=0;j<3;j++)w.add({48,FL,ccross+j,h+j});
 frame(ccross,tracematrix3,true);
 measureword(h,3);inverse3_debt(nn,MB);
 measureword(nn,6);norm_debt(a0,a1,3,kap3,rank3,MB);pay(a0,c1,rank3,MB+3);pay(a1,c0,rank3,MB+3);
 frame(c,basis6,false);frame(n,basis6,false);
 masked_num(p,mask);
 measureword(n,12);norm_debt(a,b,6,kap6,rank6,MB);pay(a,v,rank6,MB+6);pay(b,u,rank6,MB+6);
 masked_num(p,mask);frame(d,basis12,false);root_toggle(f);
}
void phase(int count){
 L sc[35];for(int j=1;j<35;j++)sc[j]=elimination(frobcols(12,1,ex[j]));
 for(int l=0;l<count;l++){
  int c=power(ex[l],35);
  for(int j=3;j<35;j+=2)xorword(12*j,12);w.constant(12,c);
  for(int j=2;j<35;j+=2)xorword(12*j,0);xorword(12,0);
  for(int j=1;j<35;j++)xorword(420+12*j,420);
  trace_kernel(0,12,420,l*12);
  for(int j=1;j<35;j++)xorword(420+12*j,420);xorword(12,0);for(int j=2;j<35;j+=2)xorword(12*j,0);w.constant(12,c);for(int j=3;j<35;j+=2)xorword(12*j,12);
  for(int j=1;j<35;j++){apply(sc[j],12*j,false);apply(sc[j],420+12*j,false);}
 }
 if(count!=4095)for(int j=1;j<35;j++){L e=elimination(frobcols(12,1,power(ex[j],count)));apply(e,12*j,true);apply(e,420+12*j,true);}
 for(int j=MB;j<=PB;j++)clearb(j);
}
'''+s[b:]
s=s.replace("init_towers();","init_towers();init_ranks();init_masks();")
# add independent phase test mode for direct D,N only, but final acceptance is full raw syndrome.
s=s.replace('if(mode=="prefix")','if(mode=="phase"){phase(4095);}else if(mode=="prefix")')
# clear private classical measurements even when mode=full ends in the inverse
s=s.replace("w.save(argv[2]);","for(int j=MB;j<=PB;j++)clearb(j);w.save(argv[2]);")
p.write_text(s)
p=Path("build.py");s=p.read_text();s=s.replace('replace("Q=851","Q=900")','replace("Q=851","Q=900").replace("HM=49141","HM=49152")');p.write_text(s)
p=Path("finalize.py");s=p.read_text().replace("49140","49153");p.write_text(s)
