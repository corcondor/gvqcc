#include <set>
#include <tuple>
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



