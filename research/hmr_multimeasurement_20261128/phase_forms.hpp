#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
using namespace std; using U=uint32_t; using L=uint64_t;
struct Packet{const char*ptr=nullptr;L len=0;};
struct Gate{unsigned char op;U a=0,b=0,t=0,bit=0,cond=0;};
struct Reader{
 char*data;L size;U Q,B,Nreg;L counts[9];array<Packet,12>P;vector<Packet>regs;L idx[12]={};
 Reader(string p){int fd=open(p.c_str(),O_RDONLY);assert(fd>=0);struct stat st;fstat(fd,&st);size=st.st_size;data=(char*)mmap(nullptr,size,PROT_READ,MAP_PRIVATE,fd,0);assert(data!=MAP_FAILED);close(fd);assert((unsigned char)data[0]==0xd7);U h[4];memcpy(h,data+16,16);assert(h[0]==2);Q=h[1];B=h[2];Nreg=h[3];memcpy(counts,data+32,72);L off=104;while(off<size){L t,n;memcpy(&t,data+off,8);memcpy(&n,data+off+8,8);off+=16;assert(t<12&&off+n<=size);if(t==0)regs.push_back({data+off,n});else{assert(!P[t].ptr);P[t]={data+off,n};}off+=n;}assert(regs.size()==Nreg&&P[1].len==counts[0]);}
 U get(int i){U x;assert((idx[i]+1)*4<=P[i].len);memcpy(&x,P[i].ptr+4*idx[i]++,4);return x;}
 Gate read(L i){Gate g;g.op=(unsigned char)P[1].ptr[i];int n=(g.op&0x30)>>4;int base=g.op&127;if(n==3){g.a=get(2);g.b=get(3);g.t=get(4);}else if(n==2){g.a=get(5);g.b=get(6);}else if(n==1)g.a=get(7);if((g.op&64)&&base!=6&&base!=7)g.bit=get(8);if(g.op&128)g.cond=get(9);return g;}
 void reset(){fill(begin(idx),end(idx),0);}
};
struct Writer{vector<unsigned char>ops;array<vector<U>,10>a;U bits;Reader&r;
 Writer(Reader&rr,U b):bits(b),r(rr){ops.reserve(rr.counts[0]);for(int i=2;i<=9;i++)a[i].reserve(rr.P[i].len/4);}
 void put(Gate g){ops.push_back(g.op);int n=(g.op&48)>>4;int base=g.op&127;if(n==3){a[2].push_back(g.a);a[3].push_back(g.b);a[4].push_back(g.t);}else if(n==2){a[5].push_back(g.a);a[6].push_back(g.b);}else if(n==1)a[7].push_back(g.a);if((g.op&64)&&base!=6&&base!=7)a[8].push_back(g.bit);if(g.op&128)a[9].push_back(g.cond);}
 void write(string p){ofstream o(p,ios::binary);assert(o);o.write(r.data,16);U h[4]={2,r.Q,bits,r.Nreg};o.write((char*)h,16);L c[9]={ops.size(),a[2].size(),a[5].size(),a[7].size(),a[8].size(),a[9].size(),r.counts[6],r.counts[7],r.counts[8]};o.write((char*)c,72);auto packet=[&](L t,const char*d,L n){o.write((char*)&t,8);o.write((char*)&n,8);if(n)o.write(d,n);};for(auto v:r.regs)packet(0,v.ptr,v.len);packet(1,(char*)ops.data(),ops.size());for(int i=2;i<=9;i++)packet(i,(char*)a[i].data(),a[i].size()*4);for(int i=10;i<=11;i++)packet(i,r.P[i].ptr,r.P[i].len);assert(o.good());}
};
#include <bitset>
#include <optional>
using V=bitset<900>;
V unit(U i){V a;a.set(i);return a;}
struct Form{V v;bool c=false;};
bool lin(Gate g){return g.op==17||g.op==33||g.op==34;}
bool diagonal(Gate g){int op=g.op&127;return op==16||op==32;}
void pull(Form&f,Gate g){if(g.op==17)f.c^=f.v[g.a];else if(g.op==33){if(f.v[g.b])f.v.flip(g.a);}else if(g.op==34){bool a=f.v[g.a];f.v[g.a]=f.v[g.b];f.v[g.b]=a;}else if(!diagonal(g))abort();}
struct Basis{vector<V> vs;vector<U> piv;vector<unsigned> codes;vector<V> echelon;
 unsigned insert(V v){unsigned x=0;V z=v;for(size_t j=0;j<echelon.size();j++)if(z[piv[j]]){z^=echelon[j];x^=codes[j];}if(z.none())return x;U i=0;while(!z[i])i++;unsigned bit=1u<<vs.size();vs.push_back(v);piv.push_back(i);echelon.push_back(z);codes.push_back(x^bit);return bit;}
 unsigned coord(V z)const{unsigned x=0;for(size_t j=0;j<echelon.size();j++)if(z[piv[j]]){z^=echelon[j];x^=codes[j];}assert(z.none());return x;}};
unsigned parity(unsigned n){return __builtin_parity(n);}
vector<unsigned> span(array<unsigned,3> a){vector<unsigned> s;for(unsigned j=1;j<8;j++){unsigned v=0;for(int i=0;i<3;i++)if(j>>i&1)v^=a[i];s.push_back(v);}sort(s.begin(),s.end());return s;}
