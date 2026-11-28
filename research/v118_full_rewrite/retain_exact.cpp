#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <unordered_map>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
using namespace std;
using U=uint32_t; using L=uint64_t; using F=vector<U>;
struct Key {F a,b; bool operator==(Key const&o)const{return a==o.a&&b==o.b;}};
struct KH {size_t operator()(Key const&k)const{L h=1469598103934665603ULL;for(auto x:k.a){h^=x;h*=1099511628211ULL;}h^=0xffffffff;for(auto x:k.b){h^=x;h*=1099511628211ULL;}return h;}};
struct Sym {
 U next=1; size_t cap; unordered_map<Key,U,KH> atoms; L trunc=0;
 Sym(size_t c):cap(c){atoms.reserve(131072);}
 F fresh(){return {next++};}
 F cut(F f){if(f.size()>cap){trunc++;return fresh();}return f;}
 F xraw(F const&a,F const&b){F r;r.reserve(a.size()+b.size());set_symmetric_difference(a.begin(),a.end(),b.begin(),b.end(),back_inserter(r));return r;}
 F x(F const&a,F const&b){if(a.empty())return b;if(b.empty())return a;return cut(xraw(a,b));}
 F neg(F a){if(!a.empty()&&a.front()==0)a.erase(a.begin());else a.insert(a.begin(),0);return a;}
 static bool one(F const&a){return a.size()==1&&a[0]==0;}
 F mul(F const&a,F const&b){if(a.empty()||b.empty())return {};if(one(a))return b;if(one(b))return a;if(a==b)return a;
   bool ac=a.front()==0,bc=b.front()==0;F A(a.begin()+ac,a.end()),B(b.begin()+bc,b.end());
   if(A==B){if(ac!=bc)return {};return a;}
   F S=xraw(A,B);array<pair<F const*,int>,3> v={{{&A,0},{&B,1},{&S,2}}};sort(v.begin(),v.end(),[](auto x,auto y){return *x.first<*y.first;});
   Key k{*v[0].first,*v[1].first};auto it=atoms.find(k);U id;if(it==atoms.end()){id=next++;if(atoms.size()>150000)atoms.clear();atoms.emplace(move(k),id);}else id=it->second;
   F r{id};int excl=v[2].second;if(excl==0)r=xraw(r,B);if(excl==1)r=xraw(r,A);if(ac)r=xraw(r,B);if(bc)r=xraw(r,A);if(ac&&bc)r.insert(r.begin(),0);return cut(move(r));
 }
 F assign(F const&old,F const&val,F const&k){if(k.empty())return old;if(one(k))return val;return x(old,mul(k,x(old,val)));}
};
struct Packet{const char*ptr=nullptr;L len=0;};
struct Gate {unsigned char op;U a=0,b=0,t=0,bit=0,cond=0;};
struct Reader {
 char*data;L size;U Q,B,Nreg;L counts[9];array<Packet,12>P;vector<Packet> regs;L idx[12]={};
 Reader(string p){int fd=open(p.c_str(),O_RDONLY);assert(fd>=0);struct stat st;fstat(fd,&st);size=st.st_size;data=(char*)mmap(nullptr,size,PROT_READ,MAP_PRIVATE,fd,0);assert(data!=MAP_FAILED);close(fd);assert((unsigned char)data[0]==0xd7);U h[4];memcpy(h,data+16,16);assert(h[0]==2);Q=h[1];B=h[2];Nreg=h[3];memcpy(counts,data+32,72);L off=104;while(off<size){L t,n;memcpy(&t,data+off,8);memcpy(&n,data+off+8,8);off+=16;assert(t<12&&off+n<=size);if(t==0)regs.push_back({data+off,n});else {assert(!P[t].ptr);P[t]={data+off,n};}off+=n;}assert(regs.size()==Nreg&&P[1].len==counts[0]);}
 U get(int i){U x;assert((idx[i]+1)*4<=P[i].len);memcpy(&x,P[i].ptr+4*idx[i]++,4);return x;}
 Gate read(L i){Gate g;g.op=(unsigned char)P[1].ptr[i];int n=(g.op&0x30)>>4;int base=g.op&127;if(n==3){g.a=get(2);g.b=get(3);g.t=get(4);}else if(n==2){g.a=get(5);g.b=get(6);}else if(n==1)g.a=get(7);if((g.op&64)&&base!=6&&base!=7)g.bit=get(8);if(g.op&128)g.cond=get(9);return g;}
 void reset(){fill(begin(idx),end(idx),0);}
};
struct Edit{L i;vector<Gate> replacement;string reason;};
struct Writer {vector<unsigned char> ops;array<vector<U>,10> a;U bits;Reader&r;
 Writer(Reader&rr,U b):bits(b),r(rr){ops.reserve(rr.counts[0]);for(int i=2;i<=9;i++)a[i].reserve(rr.P[i].len/4);}
 void put(Gate g){ops.push_back(g.op);int n=(g.op&48)>>4;int base=g.op&127;if(n==3){a[2].push_back(g.a);a[3].push_back(g.b);a[4].push_back(g.t);}else if(n==2){a[5].push_back(g.a);a[6].push_back(g.b);}else if(n==1)a[7].push_back(g.a);if((g.op&64)&&base!=6&&base!=7)a[8].push_back(g.bit);if(g.op&128)a[9].push_back(g.cond);}
 void write(string p){ofstream o(p,ios::binary);assert(o);o.write(r.data,16);U h[4]={2,r.Q,bits,r.Nreg};o.write((char*)h,16);L c[9]={ops.size(),a[2].size(),a[5].size(),a[7].size(),a[8].size(),a[9].size(),r.counts[6],r.counts[7],r.counts[8]};o.write((char*)c,72);auto packet=[&](L t,const char*d,L n){o.write((char*)&t,8);o.write((char*)&n,8);if(n)o.write(d,n);};for(auto v:r.regs)packet(0,v.ptr,v.len);packet(1,(char*)ops.data(),ops.size());for(int i=2;i<=9;i++)packet(i,(char*)a[i].data(),a[i].size()*4);for(int i=10;i<=11;i++)packet(i,r.P[i].ptr,r.P[i].len);assert(o.good());}
};

struct Prev{L i;Gate g;vector<U> zeros;};
int main(int argc,char**argv){assert(argc>=4);Reader r(argv[1]);size_t cap=argc>4?atoi(argv[4]):96;L period=argc>5?atoi(argv[5]):20000;Sym s(cap);vector<F> q(r.Q),b(r.B);for(U i=0;i<min(r.Q,840U);i++)q[i]=s.fresh();for(U i=0;i<r.B;i++)b[i]=s.fresh();
 vector<F> stack{{0}};vector<Edit> edits;map<F,Prev> prev;vector<int64_t> last(r.Q,-1),loan(r.Q,-1);L nextcut=period,repeat=0,unavailable=0,links=0,paid=0;U newbit=r.B;
 auto with=[&](unsigned char op,U a=0,U b=0,U t=0,U bit=0,U cond=0){return Gate{op,a,b,t,bit,cond};};
 auto rebase=[&](){map<F,F> seen;for(auto &v:q){if(v.empty()||Sym::one(v))continue;bool neg=v[0]==0;F f(v.begin()+neg,v.end());auto it=seen.find(f);if(it==seen.end())it=seen.emplace(f,s.fresh()).first;v=neg?s.neg(it->second):it->second;}for(auto &v:b)if(!v.empty()&&!Sym::one(v))v=s.fresh();s.atoms.clear();prev.clear();};
 for(L i=0;i<r.counts[0];i++){if(i>=nextcut&&stack.size()==1){rebase();nextcut=i+period;}Gate g=r.read(i);int op=g.op&127;bool own=g.op&128;if(g.op==0x81){stack.push_back(s.mul(stack.back(),b[g.cond]));continue;}if(g.op==1){assert(stack.size()>1);stack.pop_back();continue;}F k=own?s.mul(stack.back(),b[g.cond]):stack.back();U a=g.a,d=g.b,t=g.t;
 switch(op){
 case 0x11:q[a]=s.x(q[a],k);break;
 case 0x12:q[a]=s.assign(q[a],{},k);break;
 case 0x21:q[d]=s.x(q[d],s.mul(q[a],k));break;
 case 0x22:{F delta=s.mul(k,s.x(q[a],q[d]));q[a]=s.x(q[a],delta);q[d]=s.x(q[d],delta);break;}
 case 0x31:{paid++;F p=s.mul(q[a],q[d]);if(!own&&stack.size()==1&&Sym::one(k)&&!p.empty()&&!Sym::one(p)){
 auto it=prev.find(p);bool used=false;if(it!=prev.end()){repeat++;Prev const&v=it->second;int w=-1;for(U z:v.zeros){if(z!=a&&z!=d&&z!=t&&last[z]<(int64_t)v.i&&loan[z]<(int64_t)v.i&&q[z].empty()){w=z;break;}}if(w>=0){U m=newbit++;edits.push_back({v.i,{with(0x31,v.g.a,v.g.b,w),with(0x21,w,v.g.t)},"retain_start"});edits.push_back({i,{with(0x21,w,t),with(0x50,w,0,0,m),with(0xa0,a,d,0,0,m)},"retain_end"});loan[w]=i;links++;prev.erase(it);used=true;}else unavailable++;}
 if(!used){Prev v{i,g,{}};for(U w=0;w<r.Q;w++)if(w!=a&&w!=d&&w!=t&&q[w].empty())v.zeros.push_back(w);prev[p]=move(v);}}
 q[t]=s.x(q[t],s.mul(k,p));break;}
 case 0x30:paid++;break;
 case 0x32:{paid++;F p=s.mul(q[a],s.x(q[d],q[t]));F delta=s.mul(k,p);q[d]=s.x(q[d],delta);q[t]=s.x(q[t],delta);break;}
 case 0x50:{q[a]=s.assign(q[a],{},k);b[g.bit]=s.assign(b[g.bit],s.fresh(),k);break;}
 case 0x40:b[g.bit]=s.assign(b[g.bit],{},k);break;
 case 0x41:b[g.bit]=s.assign(b[g.bit],{0},k);break;
 case 0x42:b[g.bit]=s.x(b[g.bit],k);break;
 case 0:case 6:case 0x10:case 0x20:break;
 default:cerr<<"unsupported "<<op<<" at "<<i<<endl;return 2;
 }
 int n=(g.op&48)>>4;if(n>=1)last[a]=i;if(n>=2)last[d]=i;if(n==3)last[t]=i;
 if(i%5000000==0)cerr<<"scan "<<i<<" links "<<links<<" repeats "<<repeat<<" trunc "<<s.trunc<<endl;
 }
 assert(stack.size()==1);cerr<<"paid "<<paid<<" repeat "<<repeat<<" unavailable "<<unavailable<<" links "<<links<<" trunc "<<s.trunc<<endl;
 sort(edits.begin(),edits.end(),[](auto&a,auto&b){return a.i<b.i;});for(size_t i=1;i<edits.size();i++)assert(edits[i-1].i<edits[i].i);
 ofstream log(argv[3]);log<<"op\treason\treplacement\n";for(auto&e:edits){log<<e.i<<'\t'<<e.reason<<'\t';for(auto g:e.replacement)log<<(int)g.op<<','<<g.a<<','<<g.b<<','<<g.t<<','<<g.bit<<','<<g.cond<<';';log<<'\n';}log.close();r.reset();Writer w(r,newbit);size_t j=0;for(L i=0;i<r.counts[0];i++){Gate g=r.read(i);if(j<edits.size()&&edits[j].i==i){for(auto e:edits[j++].replacement)w.put(e);}else w.put(g);}assert(j==edits.size());w.write(argv[2]);cerr<<"out ops "<<w.ops.size()<<" static paid "<<w.a[2].size()<<endl;
}
