// Exact original 316K prelude + new total core. No syndrome-based host choices.
// Preserve every original instruction before first CCX; pull its linear phase
// into a classical residual mask and return the original quantum coordinate frame.
#include "native.hpp"
#include <bitset>
#include <functional>
int ex[8190],lg[4096],dual[4096],maskof[4096];
int mul(int a,int b){return a&&b?ex[lg[a]+lg[b]]:0;}
int inv(int a){assert(a);return ex[4095-lg[a]];}
int tr(int a){int z=0;for(int i=0;i<12;i++){z^=a;a=mul(a,a);}assert(z==0||z==1);return z;}
vector<int> prod(vector<int>a,vector<int>b){vector<int>c(a.size()+b.size()-1);for(int i=0;i<(int)a.size();i++)for(int j=0;j<(int)b.size();j++)c[i+j]^=mul(a[i],b[j]);return c;}
int ev(vector<int>const&a,int x){int z=0;for(auto i=a.rbegin();i!=a.rend();++i)z=mul(z,x)^*i;return z;}
using Word=array<U,12>;
struct ABI{vector<U>S,E;vector<U>work;};
ABI abi(Reader&r){
 ABI a;a.S.resize(840);a.E.resize(49140);vector<bool>seen(r.Q);
 for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);string name(p.ptr+8,n);assert(l==12);U i=stoul(name.substr(1));assert(name[0]=='S'||name[0]=='E');auto&v=name[0]=='S'?a.S:a.E;
  for(U j=0;j<l;j++){U q;memcpy(&q,p.ptr+8+n+4*j,4);assert(bool(q>>31)==(name[0]=='S'));q&=0x7fffffff;v.at(i*12+j)=q;if(name[0]=='S')seen.at(q)=true;}}
 for(U q=0;q<r.Q;q++)if(!seen[q])a.work.push_back(q);return a;
}
int main(int argc,char**argv){
 assert(argc==4);Reader r(argv[1]),core(argv[2]);assert(r.Q==900&&r.counts[0]==69782188&&r.counts[1]==318972);
 ABI a=abi(r),b=abi(core);assert(core.Q<=900&&core.counts[6]==0);
 U orig=r.B,mask=orig+49140,K=mask+49140,cf=K+840,active=cf+71*12,base=active+1;
 Writer w(r,base+core.B);
 auto zero=[&](U x){w.put({64,0,0,0,x});};
 auto flip=[&](U x){w.put({66,0,0,0,x});};
 auto xorif=[&](U x,U c){w.put({194,0,0,0,x,c});};
 auto cw=[&](U p,int j){Word a;for(int k=0;k<12;k++)a[k]=p+12*j+k;return a;};
 for(U j=0;j<49140;j++){zero(orig+j);xorif(orig+j,a.E[j]);}
 for(U j=0;j<840;j++)zero(K+j);
 vector<bitset<840>> v(r.Q);for(U j=0;j<840;j++)v[a.S[j]].set(j);
 vector<Gate> lin;L cut=0,zcount=0;
 for(L i=0;i<r.counts[0];i++){
  auto g=r.read(i);int op=g.op&127,n=(g.op&48)>>4;
  if(op==49){cut=i;break;}
  if(n==0||op>=64){w.put(g);assert(n==0);continue;}
  if(op==33||op==34){assert(!(g.op&128));w.put(g);lin.push_back(g);if(op==33)v[g.b]^=v[g.a];else swap(v[g.a],v[g.b]);continue;}
  if(op==16){w.put(g);zcount++;
   for(U j=0;j<840;j++)if(v[g.a].test(j)){if(g.op&128)xorif(K+j,g.cond);else flip(K+j);}
   continue;
  }
  cerr<<"Unexpected quantum operation before cut "<<i<<" "<<op<<endl;return 2;
 }
 assert(cut&&zcount>0&&lin.size()>0);
 // Undo only the original linear coordinates. Phase already applied.
 for(auto it=lin.rbegin();it!=lin.rend();++it)w.put(*it);
 for(U j=0;j<49140;j++){zero(a.E[j]);xorif(a.E[j],orig+j);zero(mask+j);xorif(mask+j,orig+j);}
 // Exact trace dual coordinate polynomial of the prefix phase.
 int x=1;for(int i=0;i<4095;i++){ex[i]=ex[i+4095]=x;lg[x]=i;x<<=1;if(x&4096)x^=0x1053;}assert(x==1);
 vector<bool>seen(4096);for(int z=0;z<4096;z++){int v=0;for(int j=0;j<12;j++)v|=tr(mul(z,1<<j))<<j;assert(!seen[v]);seen[v]=true;maskof[z]=v;dual[v]=z;}
 auto mat=[&](int c){Word m;for(int j=0;j<12;j++)m[j]=maskof[mul(c,dual[1<<j])];return m;};
 auto accum=[&](Word const&a,Word const&b,int c){if(!c)return;auto m=mat(c);for(int j=0;j<12;j++)for(int k=0;k<12;k++)if(m[j]>>k&1)xorif(b[k],a[j]);};
 vector<vector<int>> T,NB(71);vector<int>L0{0,1};NB[0]={1};
 for(int k=0;k<7;k++){int v=ev(L0,1<<k);assert(v);auto t=L0;for(auto &a:t)a=mul(a,inv(v));T.push_back(t);vector<int>u(2*L0.size()-1);for(int j=0;j<(int)L0.size();j++){u[2*j]^=mul(L0[j],L0[j]);u[j]^=mul(v,L0[j]);}L0=u;}
 for(int i=1;i<=70;i++){int k=__builtin_ctz((unsigned)i);NB[i]=prod(NB[i^(1<<k)],T[k]);assert(NB[i].size()==size_t(i+1));}
 for(int i=0;i<71;i++)for(U p:cw(cf,i))zero(p);
 for(int j=0;j<70;j++){vector<int>p(71);p[j+1]=1;for(int i=70;i>=0;i--){int c=mul(p[i],inv(NB[i].back()));accum(cw(K,j),cw(cf,i),c);for(int k=0;k<=i;k++)p[k]^=mul(c,NB[i][k]);}assert(all_of(p.begin(),p.end(),[](int x){return !x;}));}
 function<void(int,int,int)> scan=[&](int k,int off,int deg){
  if(!k){if(off)accum(cw(cf,0),cw(mask,lg[off]),1);return;}
  int h=1<<(k-1);if(deg<h){scan(k-1,off,deg);scan(k-1,off^h,deg);return;}
  int t=ev(T[k-1],off);for(int i=h;i<=deg;i++)accum(cw(cf,i),cw(cf,i-h),t);
  scan(k-1,off,h-1);for(int i=h;i<=deg;i++)accum(cw(cf,i),cw(cf,i-h),1);
  scan(k-1,off^h,h-1);for(int i=h;i<=deg;i++)accum(cw(cf,i),cw(cf,i-h),t^1);
 };scan(12,0,70);
 L preops=w.ops.size();
 vector<U> qm(core.Q),bm(core.B);for(U j=0;j<core.B;j++)bm[j]=base+j;
 for(U j=0;j<840;j++)qm[b.S[j]]=a.S[j];for(U j=0;j<b.work.size();j++)qm[b.work[j]]=a.work[j];for(U j=0;j<49140;j++)bm[b.E[j]]=mask+j;
 auto cb=[&](U x){return bm.at(x&0x7fffffff)|(x&0x80000000);};
 // The residual is public classical data. If its entire value is zero,
 // the exact residual oracle is identity even for arbitrary legal S.
 zero(active);
 for(U j=0;j<49140;j++)w.put({193,0,0,0,active,mask+j});
 w.put({129,0,0,0,0,active});
 for(L i=0;i<core.counts[0];i++){
  auto g=core.read(i);int op=g.op&127,n=(g.op&48)>>4;if(op==6)continue;
  if(n){g.a=qm.at(g.a);if(n>=2)g.b=qm.at(g.b);if(n==3)g.t=qm.at(g.t);}
  if((g.op&64)&&op!=6&&op!=7)g.bit=cb(g.bit);if(g.op&128)g.cond=cb(g.cond);w.put(g);
 }
 w.put({1});zero(active);
 // All public mask bits were restored before the core. Only private classical state remains.
 vector<bool> publicE(r.B);for(U j:a.E)publicE[j]=true;for(U j=0;j<r.B;j++)if(!publicE[j])zero(j);
 for(U j=r.B;j<w.bits;j++)zero(j);
 w.write(argv[3]);cerr<<"parent_cut "<<cut<<" prefix_z "<<zcount<<" prefix_linear "<<lin.size()<<" physical_shell_ops "<<preops<<" core_ops "<<core.counts[0]<<" full_ops "<<w.ops.size()<<" full_paid "<<w.a[2].size()<<"\n";
}

