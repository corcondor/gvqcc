#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <vector>
#include <utility>
#include <numeric>
#include <functional>
using namespace std;using U=uint64_t;using I=uint32_t; constexpr int N=35,F=4096,M=4095,Q=900,FLAG=49140,HM=49967;
int ex[2*M],lg[F];int mul(int a,int b){return a&&b?ex[lg[a]+lg[b]]:0;}int inv(int a){assert(a);return ex[M-lg[a]];}int power(int a,int i){return a?ex[(lg[a]*i)%M]:!i;}
struct G{int t,a=-1,b=-1,c=-1;I m=0,k=0;};
struct W{vector<uint8_t> c[10];map<int,U> counts;U cc=0;void push(int j,I x){auto p=(uint8_t*)&x;c[j].insert(c[j].end(),p,p+4);}void add(G g){c[1].push_back(g.t);counts[g.t]++;int ar=(g.t>>4)&3;switch(ar){case 1:push(7,g.a);break;case 2:push(5,g.a);push(6,g.b);break;case 3:push(2,g.a);push(3,g.b);push(4,g.c);cc++;break;}if(g.t&64)push(8,g.m);if(g.t&128)push(9,g.k);}void cx(int a,int b){assert(a!=b);add({33,a,b});}void x(int a){add({17,a});}void sw(int a,int b){if(a!=b)add({34,a,b});}void fieldadd(int s,int dst,int v){if(!v)return;
 static vector<pair<int,int>> prep[F];static array<int,12> row[F];static bool done[F]{};
 if(!done[v]){done[v]=true;for(int a=0;a<12;a++){int z=mul(1<<a,v);for(int b=0;b<12;b++)if(z>>b&1)row[v][b]|=1<<a;}
 for(;;){int gain=0,bi=-1,bj=-1;for(int i=0;i<12;i++)for(int j=0;j<12;j++)if(i!=j){int g=-2;for(auto r:row[v])if(r>>j&1)g+=(r>>i&1)?1:-1;if(g>gain){gain=g;bi=i;bj=j;}}if(!gain)break;prep[v].push_back({bi,bj});for(int&r:row[v])if(r>>bj&1)r^=1<<bi;}}
 for(auto [a,b]:prep[v])cx(s+a,s+b);for(int b=0;b<12;b++)for(int a=0;a<12;a++)if(row[v][b]>>a&1)cx(s+a,dst+b);for(auto it=prep[v].rbegin();it!=prep[v].rend();++it)cx(s+it->first,s+it->second); }void constant(int dst,int v){for(int b=0;b<12;b++)if(v>>b&1)x(dst+b);}void scale(int q,int v){if(v==1)return;assert(v);int rows[12]={};for(int i=0;i<12;i++){int z=mul(1<<i,v);for(int j=0;j<12;j++)if(z>>j&1)rows[j]|=1<<i;}vector<G> g;for(int j=0;j<12;j++){int r=j;while(r<12&&!(rows[r]>>j&1))r++;assert(r<12);if(r!=j){swap(rows[r],rows[j]);g.push_back({34,q+r,q+j});}for(int i=0;i<12;i++)if(i!=j&&(rows[i]>>j&1)){rows[i]^=rows[j];g.push_back({33,q+j,q+i});}}for(int i=0;i<12;i++)assert(rows[i]==1<<i);for(auto it=g.rbegin();it!=g.rend();it++)add(*it);}
 void save(string name){ofstream f(name,ios::binary);unsigned char magic[]={0xd7,0x50,0xc7,0xd5,0xc3,0x29,0xd3,0x26,0xe3,0xcc,0x9f,0x68,0x34,0xf2,0xb8,0xbf};f.write((char*)magic,16);I h[4]={2,Q,HM+1,2*N+M};f.write((char*)h,16);U hs[]={c[1].size(),cc,c[5].size()/4,c[7].size()/4,c[8].size()/4,c[9].size()/4,0,0,0};f.write((char*)hs,72);auto reg=[&](string name,int start,bool qu){U kind=0,size=8+name.size()+48;I n=name.size(),r=12;f.write((char*)&kind,8);f.write((char*)&size,8);f.write((char*)&n,4);f.write((char*)&r,4);f.write(name.data(),n);for(int j=0;j<12;j++){I w=start+j;if(qu)w|=0x80000000;f.write((char*)&w,4);}};for(int i=0;i<N;i++)reg("S"+to_string(i),i*12,true);for(int i=0;i<N;i++)reg("S"+to_string(i+35),420+i*12,true);for(int i=0;i<M;i++)reg("E"+to_string(i),i*12,false);for(U k=1;k<=9;k++){U n=c[k].size();f.write((char*)&k,8);f.write((char*)&n,8);f.write((char*)c[k].data(),n);}U trailer[]={10,0,11,8,0};f.write((char*)trailer,40);cout<<name<<" Q="<<Q<<" paid="<<cc<<" ops="<<c[1].size()<<" CX="<<counts[33]<<" SWAP="<<counts[34]<<" HMR="<<counts[80]<<endl;}
};
#include "templates.hpp"
W w;
constexpr int H=840, FQ=875, A=876, BQ=888;
void cc(int a,int b,int c){assert(a!=b&&a!=c&&b!=c);w.add({49,a,b,c});}
void cx(int a,int b){w.cx(a,b);}
void fs(int a,int b,int f){if(a==b)return;cx(a,b);cc(f,b,a);cx(a,b);}
void cwx(int a,int b,int f=FQ){for(int j=0;j<12;j++)cc(f,a+j,b+j);}
void cws(int a,int b){for(int j=0;j<12;j++)fs(a+j,b+j,FQ);}
void mx(int a,int b,int t){assert(a!=b&&a!=t&&b!=t);int q[36];for(int i=0;i<12;i++){q[i]=a+i;q[12+i]=b+i;q[24+i]=t+i;}for(int c:CODES){int x=q[c%64],y=q[(c/64)%64];if(c<4096)cx(x,y);else cc(x,y,q[c/4096-1]);}}
void inv12(int x,bool ctrl=false){int q[30];for(int j=0;j<12;j++)q[j]=x+j;for(int j=0;j<18;j++)q[12+j]=A+j;
 for(auto &g:IT){int a=q[g[1]],b=q[g[2]],c=q[g[3]];if(!ctrl){if(g[0]==0)w.x(a);else if(g[0]==1)cx(a,b);else cc(a,b,c);}else{if(g[0]==0)cx(FQ,a);else if(g[0]==1)cc(FQ,a,b);else{cc(FQ,a,894);cc(894,b,c);cc(FQ,a,894);}}}}
void frob(int q,int e){int rows[12]={};for(int i=0;i<12;i++){int z=power(1<<i,e);for(int j=0;j<12;j++)if(z>>j&1)rows[j]|=1<<i;}vector<G> g;
 for(int j=0;j<12;j++){int r=j;while(r<12&&!(rows[r]>>j&1))r++;assert(r<12);if(r!=j){swap(rows[r],rows[j]);g.push_back({34,q+r,q+j});}for(int i=0;i<12;i++)if(i!=j&&(rows[i]>>j&1)){rows[i]^=rows[j];g.push_back({33,q+j,q+i});}}
 for(auto it=g.rbegin();it!=g.rend();++it)w.add(*it);}
void fmx(int t,int a,int b,int d){if(a==b){for(int j=0;j<12;j++)cx(a+j,BQ+j);b=BQ;frob(b,d);mx(a,b,A);cwx(A,t);mx(a,b,A);frob(b,4096/d);for(int j=0;j<12;j++)cx(a+j,b+j);}
 else{frob(b,d);mx(a,b,A);cwx(A,t);mx(a,b,A);frob(b,4096/d);}}
void fx(int t,int a,int d){for(int i=0;i<12;i++){int z=power(1<<i,d);for(int j=0;j<12;j++)if(z>>j&1)cc(FQ,a+i,t+j);}}
void cmx(int a,int b,int t){mx(a,b,A);cwx(A,t);mx(a,b,A);}
void phase_tmp(int b,int t,bool inactive){if(inactive)w.x(FQ);for(int j=0;j<12;j++)w.add({160,FQ,t+j,-1,0,I(b+j)});if(inactive)w.x(FQ);}
void hmr(int b,int t){for(int j=0;j<12;j++)w.add({80,t+j,-1,-1,I(b+j)});}
void clearbits(int b){for(int j=0;j<12;j++)w.add({64,-1,-1,-1,I(b+j)});}
// Clean multi-controlled X, using only the 24 clean workspace bits.
void mc(const vector<int>& c,int t,int start=A){int n=c.size();if(n==0){w.x(t);return;}if(n==1){cx(c[0],t);return;}if(n==2){cc(c[0],c[1],t);return;}
 if(n<=24){cc(c[0],c[1],start);for(int j=2;j<n-1;j++)cc(start+j-2,c[j],start+j-1);cc(start+n-3,c[n-1],t);for(int j=n-2;j>=2;j--)cc(start+j-2,c[j],start+j-1);cc(c[0],c[1],start);return;}
 int m=n/2;vector<int> c1(c.begin(),c.begin()+m),c2(c.begin()+m,c.end());c2.push_back(start);mc(c1,start,start+1);mc(c2,t,start+1);mc(c1,start,start+1);
}
void pred(vector<int> pos,vector<int> neg,int t=FQ){for(int b:neg)w.x(b);pos.insert(pos.end(),neg.begin(),neg.end());mc(pos,t);for(int b:neg)w.x(b);}
vector<int> act(int i){return i?vector<int>{H+i-1}:vector<int>{};}
void adj(int i,int k){auto p=act(i);p.push_back(H+i+k-1);vector<int> n;for(int j=0;j<k-1;j++)n.push_back(H+i+j);pred(p,n);}
void terminal(int i){auto p=act(i);vector<int> n;for(int j=i;j<35;j++)n.push_back(H+j);pred(p,n);}
void valid(int i,int j){int m=35-i,n=2*m;for(int k=1;k<=min(m,n-j);k++){if(i)cc(H+i-1,H+i+k-1,FQ);else cx(H+k-1,FQ);}}
void atleast(int i,int l){auto p=act(i);vector<int> n;for(int k=0;k<max(0,l-1);k++)n.push_back(H+i+k);pred(p,n);terminal(i);}
void mark(int i,bool rev){int m=35-i,p=2*i;auto a=act(i);
 auto prefix=[&](int j){auto c=a;if(j)c.push_back(H+i+j-1);vector<int> z;for(int b=0;b<12;b++)z.push_back(12*(p+j)+b);pred(c,z,H+i+j);};
 auto diff=[&](int j){if(j){if(i)cc(H+i-1,H+i+j-1,H+i+j);else cx(H+j-1,H+j);}else if(i)cx(H+i-1,H+i);else w.x(H);};
 if(!rev){for(int j=0;j<m;j++)prefix(j);for(int j=m-1;j>=0;j--)diff(j);}
 else{for(int j=0;j<m;j++)diff(j);for(int j=m-1;j>=0;j--)prefix(j);}}
void perm(int p,vector<int> o,bool rev=false){int n=o.size();vector<int> cur(n),pos(n);iota(cur.begin(),cur.end(),0);pos=cur;vector<pair<int,int>> s;for(int j=0;j<n;j++){int k=pos[o[j]];if(j!=k){s.push_back({p+j,p+k});int u=cur[j],v=cur[k];swap(cur[j],cur[k]);pos[u]=k;pos[v]=j;}}if(rev)reverse(s.begin(),s.end());for(auto [a,b]:s)cws(12*a,12*b);}
vector<int> rot(int n,int k){vector<int> o;for(int j=0;j<n;j++)o.push_back((j+k-1)%n);return o;}
vector<int> po(int n,int k){int r=n-k;vector<int> o;for(int j=k;j<2*k;j++)o.push_back(j);for(int j=2*n-1;j>=2*k+r;j--)o.push_back(j);for(int j=2*k+r-1;j>=2*k;j--)o.push_back(j);for(int j=0;j<k-1;j++)o.push_back(j);o.push_back(k-1);assert(int(o.size())==2*n);return o;}
vector<int> oo(int n,int k){vector<int> o;for(int j=n-1;j>=0;j--)o.push_back(j);for(int j=2*n-k-1;j>=n;j--)o.push_back(j);for(int j=2*n-1;j>=2*n-k;j--)o.push_back(j);assert(int(o.size())==2*n);return o;}
// HMR debt: after controlled swap, old temporary is scalar*T if inactive,
// or inverse(scalar)*T if active. Repay both cases, clear all classical bits.
void scalebatch(int s,const vector<int>& ts,bool inverse,const function<void(int)>& flag){if(ts.empty())return;if(inverse)inv12(s);
 for(int j=0;j<(int)ts.size();j++){int t=ts[j],m=49140+12*j;flag(j);mx(s,t,A);cws(t,A);hmr(m,A);mx(s,t,A);phase_tmp(m,A,true);mx(s,t,A);flag(j);}
 inv12(s);
 for(int j=0;j<(int)ts.size();j++){int t=ts[j],m=49140+12*j;flag(j);mx(s,t,A);phase_tmp(m,A,false);mx(s,t,A);clearbits(m);flag(j);}
 inv12(s);if(inverse)inv12(s);}
void recip(int i,bool rev){int m=35-i,n=2*m,p=2*i;for(int k=1;k<=m;k++){adj(i,k);perm(p,rot(n,k));adj(i,k);}
 vector<int> ts;for(int j=1;j<n;j++)ts.push_back(12*(p+j));auto flag=[&](int j){valid(i,j+1);};
 auto fr=[&](int d,int j,int k){valid(i,j);int t=12*(p+j),a=12*(p+k);if(j==d*k)fx(t,a,d);else fmx(t,12*(p+j-d*k),a,d);valid(i,j);};
 if(!rev){scalebatch(12*p,ts,true,flag);for(int d:{2,4,16})for(int j=n-1;j>=d;j--)for(int k=1;k<=j/d;k++)fr(d,j,k);valid(i,0);inv12(12*p,true);valid(i,0);scalebatch(12*p,ts,false,flag);}
 else{scalebatch(12*p,ts,true,flag);valid(i,0);inv12(12*p,true);valid(i,0);for(int d:{16,4,2})for(int j=d;j<n;j++)for(int k=j/d;k>=1;k--)fr(d,j,k);scalebatch(12*p,ts,false,flag);}
 for(int k=1;k<=m;k++){adj(i,k);perm(p,rot(n,k),true);adj(i,k);}}
void pack(int i,bool rev){int n=35-i,p=2*i,a=p+n,lead=p+2*n-1;for(int k=1;k<=n;k++){adj(i,k);perm(p,rev?oo(n,k):po(n,k),rev);adj(i,k);}
 auto shear=[&](int l){atleast(i,l);int q=l?p+l-1:lead;for(int t=0;t<n-l;t++)if(a+t!=lead)cmx(12*q,12*(a+t),12*(p+l+t));atleast(i,l);};
 vector<int> ts;for(int j=p;j<lead;j++)ts.push_back(12*j);auto flag=[&](int){atleast(i,0);};
 if(!rev){for(int l=n;l>=0;l--)shear(l);scalebatch(12*lead,ts,true,flag);atleast(i,0);inv12(12*lead,true);atleast(i,0);}
 else{atleast(i,0);inv12(12*lead,true);atleast(i,0);scalebatch(12*lead,ts,false,flag);for(int l=0;l<=n;l++)shear(l);}
 for(int k=1;k<=n;k++){adj(i,k);perm(p,rev?po(n,k):oo(n,k),rev);adj(i,k);}}
void pad(int i){terminal(i);vector<int> p=(35-i)%2?vector<int>{0,1}:vector<int>{1};for(int j=0;j<(35-i)/2;j++){vector<int> q(p.size()+2);for(int k=0;k<(int)p.size();k++){q[k]^=mul(p[k],KK[j]);q[k+1]^=p[k];q[k+2]^=p[k];}p=q;}for(int j=0;j<(int)p.size()-1;j++)for(int b=0;b<12;b++)if(p[j]>>b&1)cx(FQ,12*(2*i+j)+b);terminal(i);}
void codec(bool rev){if(!rev){for(int i=0;i<35;i++){mark(i,false);recip(i,false);if(i%5==0)cerr<<"extract "<<i<<" "<<w.c[1].size()<<endl;}for(int i=0;i<36;i++)pad(i);for(int i=34;i>=0;i--)pack(i,false);}
 else{for(int i=0;i<35;i++)pack(i,true);for(int i=35;i>=0;i--)pad(i);for(int i=34;i>=0;i--){recip(i,true);mark(i,true);if(i%5==0)cerr<<"restore "<<i<<" "<<w.c[1].size()<<endl;}}}
void wordxor(int a,int b){for(int j=0;j<12;j++)cx(a+j,b+j);}
void scan(int count){for(int k=0;k<count;k++){int x=ex[k];for(int j=3;j<35;j+=2)wordxor(12*j,12);w.constant(12,power(x,35));wordxor(12,0);for(int j=2;j<35;j+=2)wordxor(12*j,0);for(int j=1;j<35;j++)wordxor(420+12*j,420);
 vector<int> z;for(int b=0;b<12;b++)z.push_back(b);pred({},z);inv12(12);mx(12,420,A);phase_tmp(12*k,A,false);mx(12,420,A);inv12(12);pred({},z);
 for(int j=34;j>=1;j--)wordxor(420+12*j,420);for(int j=34;j>=2;j-=2)wordxor(12*j,0);wordxor(12,0);w.constant(12,power(x,35));for(int j=33;j>=3;j-=2)wordxor(12*j,12);
 for(int j=1;j<35;j++){w.scale(12*j,ex[j]);w.scale(420+12*j,ex[j]);}
 if(k%512==0)cerr<<"scan "<<k<<" "<<w.c[1].size()<<endl;}
 if(count%4095)for(int j=1;j<35;j++){int a=ex[(4095-(count*j)%4095)%4095];w.scale(12*j,a);w.scale(420+12*j,a);}}
int main(int argc,char**argv){int x=1;for(int i=0;i<M;i++){ex[i]=ex[i+M]=x;lg[x]=i;x<<=1;if(x&F)x^=0x1053;}assert(x==1);
 string mode=argv[1];if(mode=="forward")codec(false);else if(mode=="full"){codec(false);scan(argc>3?stoi(argv[3]):4095);codec(true);}else if(mode=="roundtrip"){codec(false);codec(true);}else assert(false);
 w.save(argv[2]);}
