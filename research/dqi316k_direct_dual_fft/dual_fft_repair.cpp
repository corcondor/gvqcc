#include "common.hpp"
#include <functional>
int ex[8190],lg[4096],dual[4096],maskof[4096];
int mul(int a,int b){return a&&b?ex[lg[a]+lg[b]]:0;}
int inv(int a){assert(a);return ex[4095-lg[a]];}
int tr(int a){int z=0;for(int i=0;i<12;i++){z^=a;a=mul(a,a);}assert(z==0||z==1);return z;}
vector<int> prod(vector<int>a,vector<int>b){vector<int>c(a.size()+b.size()-1);for(int i=0;i<(int)a.size();i++)for(int j=0;j<(int)b.size();j++)c[i+j]^=mul(a[i],b[j]);return c;}
int ev(vector<int>const&a,int x){int z=0;for(auto i=a.rbegin();i!=a.rend();++i)z=mul(z,x)^*i;return z;}
int main(int argc,char**argv){assert(argc==3);Reader r(argv[1]);assert(r.Q==900&&r.Nreg==4165);vector<array<U,12>> E(4095),S(70);vector<bool> seenE(4095),seenS(70);
 for(auto reg:r.regs){U n,k;memcpy(&n,reg.ptr,4);memcpy(&k,reg.ptr+4,4);assert(k==12);string name(reg.ptr+8,n);int i=stoi(name.substr(1));bool q=name[0]=='S';assert(q||name[0]=='E');assert(i>=0&&i<(q?70:4095));auto& dst=q?S[i]:E[i];for(int j=0;j<12;j++){U v;memcpy(&v,reg.ptr+8+n+4*j,4);assert(bool(v>>31)==q);dst[j]=v&0x7fffffff;} (q?seenS:seenE)[i]=true;}
 assert(all_of(seenS.begin(),seenS.end(),[](bool a){return a;}));assert(all_of(seenE.begin(),seenE.end(),[](bool a){return a;}));
 int a=1;for(int i=0;i<4095;i++){ex[i]=ex[i+4095]=a;lg[a]=i;a<<=1;if(a&4096)a^=0x1053;}assert(a==1);
 vector<bool>seen(4096);for(int x=0;x<4096;x++){int v=0;for(int j=0;j<12;j++)v|=tr(mul(x,1<<j))<<j;assert(!seen[v]);seen[v]=true;maskof[x]=v;dual[v]=x;}
 vector<int> p{1};for(int k=1;k<=70;k++)p=prod(p,{ex[k],1});assert(p.size()==71&&p.back()==1);for(int k=1;k<=70;k++)assert(ev(p,ex[k])==0);
 auto matrix=[&](int c){array<int,12> m;for(int k=0;k<12;k++)m[k]=maskof[mul(c,dual[1<<k])];return m;};
 array<array<int,12>,70> recurrence;for(int i=0;i<70;i++)recurrence[i]=matrix(p[i]);
 int Lg[70][70]={};for(int j=0;j<70;j++){vector<int> t{1};for(int k=0;k<70;k++)if(k!=j)t=prod(t,{ex[k],1});int d=inv(mul(ex[j],ev(t,ex[j])));for(int i=0;i<70;i++)Lg[i][j]=mul(d,t[i]);}
 for(int j=0;j<70;j++)for(int k=0;k<70;k++){int z=0;for(int i=69;i>=0;i--)z=mul(z,ex[k])^Lg[i][j];assert(mul(z,ex[k])==(j==k));}
 U pass=r.B,scratch=r.B+1,cb=r.B+13;Writer w(r,r.B+13+71*12);
 auto zero=[&](U x){w.put({64,0,0,0,x});};auto one=[&](U x){w.put({65,0,0,0,x});};auto xorif=[&](U x,U c){w.put({194,0,0,0,x,c});};auto push=[&](){w.put({129,0,0,0,0,pass});};auto pop=[&](){w.put({1});};auto clearif=[&](U x,U c){w.put({192,0,0,0,x,c});};
 auto clearword=[&](){for(int j=0;j<12;j++)zero(scratch+j);};auto add=[&](array<U,12>const&src,array<int,12>const&m){for(int j=0;j<12;j++)for(int k=0;k<12;k++)if((m[j]>>k)&1)xorif(scratch+k,src[j]);};

 // Novel polynomial basis: T_k vanishes on the low k-dimensional subspace.
 vector<vector<int>> T,NB(71);vector<int> A{0,1};NB[0]={1};
 for(int k=0;k<7;k++){int v=ev(A,1<<k);assert(v);vector<int> t=A;for(auto &x:t)x=mul(x,inv(v));T.push_back(t);vector<int> next(2*A.size()-1);for(int j=0;j<(int)A.size();j++){next[2*j]^=mul(A[j],A[j]);next[j]^=mul(v,A[j]);}A=next;}
 for(int i=1;i<=70;i++){int k=__builtin_ctz((unsigned)i);NB[i]=prod(NB[i^(1<<k)],T[k]);assert(NB[i].size()==size_t(i+1));}
 int Cn[71][70]={};
 for(int j=0;j<70;j++){vector<int> g(71);for(int i=0;i<70;i++)g[i+1]=Lg[i][j];for(int i=70;i>=0;i--){int d=mul(g[i],inv(NB[i].back()));Cn[i][j]=d;for(int k=0;k<=i;k++)g[k]^=mul(d,NB[i][k]);}assert(all_of(g.begin(),g.end(),[](int v){return !v;}));}
 auto coef=[&](int i){array<U,12> a;for(int j=0;j<12;j++)a[j]=cb+12*i+j;return a;};
 auto accumulate=[&](array<U,12>const&src,array<U,12>const&dst,int c){if(!c)return;auto m=matrix(c);for(int j=0;j<12;j++)for(int k=0;k<12;k++)if((m[j]>>k)&1)xorif(dst[k],src[j]);};
 one(pass);clearword();
 // Fast fail: one complete recurrence equation is an exact necessary condition.
 for(int k=0;k<12;k++)xorif(scratch+k,E[70][k]);for(int k=0;k<70;k++)add(E[k],recurrence[k]);for(int k=0;k<12;k++)clearif(pass,scratch+k);clearword();
 push();
 for(int i=0;i<=70;i++){auto c=coef(i);for(U x:c)zero(x);for(int j=0;j<70;j++)accumulate(E[j],c,Cn[i][j]);}
 function<void(int,int,int)> scan=[&](int k,int off,int deg){
   if(k==0){if(off){int j=lg[off];auto c=coef(0);for(int b=0;b<12;b++){xorif(scratch+b,c[b]);xorif(scratch+b,E[j][b]);clearif(pass,scratch+b);zero(scratch+b);}}return;}
   int h=1<<(k-1);
   if(deg<h){scan(k-1,off,deg);scan(k-1,off^h,deg);return;}
   int t=ev(T[k-1],off);
   for(int i=h;i<=deg;i++)accumulate(coef(i),coef(i-h),t);
   scan(k-1,off,h-1);
   for(int i=h;i<=deg;i++)accumulate(coef(i),coef(i-h),1);
   scan(k-1,off^h,h-1);
   for(int i=h;i<=deg;i++)accumulate(coef(i),coef(i-h),t^1);
 };
 scan(12,0,70);for(int i=0;i<=70;i++)for(U x:coef(i))zero(x);pop();
 push();for(int i=0;i<70;i++){for(int j=0;j<70;j++)add(E[j],matrix(Lg[i][j]));for(int k=0;k<12;k++)w.put({144,S[i][k],0,0,0,scratch+(U)k});clearword();}pop();
 w.put({66,0,0,0,pass});push();for(L i=0;i<r.counts[0];i++)w.put(r.read(i));pop();zero(pass);
 w.write(argv[2]);cerr<<"Q="<<r.Q<<" ops="<<w.ops.size()<<" paid="<<w.a[2].size()<<" added="<<w.ops.size()-r.counts[0]<<"\n";
}
