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
struct RW{U r[3],w[2];int nr=0,nw=0;bool valid=true;};
RW rw(Gate g){RW v;switch(g.op&127){case 0:case 6:case 7:break;case 0x10:v.r[v.nr++]=g.a;break;case 0x11:v.w[v.nw++]=g.a;break;case 0x20:v.r[v.nr++]=g.a;v.r[v.nr++]=g.b;break;case 0x21:v.r[v.nr++]=g.a;v.w[v.nw++]=g.b;break;case 0x22:v.r[v.nr++]=g.a;v.r[v.nr++]=g.b;v.w[v.nw++]=g.a;v.w[v.nw++]=g.b;break;case 0x30:v.r[v.nr++]=g.a;v.r[v.nr++]=g.b;v.r[v.nr++]=g.t;break;case 0x31:v.r[v.nr++]=g.a;v.r[v.nr++]=g.b;v.w[v.nw++]=g.t;break;case 0x32:v.r[v.nr++]=g.a;v.r[v.nr++]=g.b;v.r[v.nr++]=g.t;v.w[v.nw++]=g.b;v.w[v.nw++]=g.t;break;default:v.valid=false;}return v;}
L key(Gate g){int o=g.op&127;U a=g.a,b=g.b,t=g.t;if(o==0x20||o==0x31){if(a>b)swap(a,b);}if(o==0x30){array<U,3>x{a,b,t};sort(x.begin(),x.end());a=x[0];b=x[1];t=x[2];}assert(a<1024&&b<1024&&t<1024&&(g.cond&0x7fffffff)<(1<<21));L c=(g.cond&0x7fffffff)|((g.cond>>31)<<21);return (c<<38)|(L(g.op)<<30)|(L(t)<<20)|(L(b)<<10)|a;}
int main(int argc,char**argv){assert(argc==3);Reader r(argv[1]);assert(r.Q==900&&r.counts[0]==69782188);vector<bool>del(r.counts[0]);set<L>dead={33358003,33358011,33358016,33358027,33358037,33358047,33358053,33358061,33358068,33358079,37473965,37473966,37473967,37473968,37473969,37473970,37473971,37473972,37473973,37473974};vector<L>rr(r.Q),ww(r.Q);L barrier=0;unordered_map<L,L>last;map<int,L>hist;
for(L i=0;i<r.counts[0];i++){Gate g=r.read(i);int o=g.op&127;L k=i+1;if(dead.count(i)){assert(o==0x31||o==0x30);del[i]=true;hist[256+o]++;continue;}RW a=rw(g);if(!a.valid){barrier=k;continue;}bool candidate=o==0x10||o==0x11||o==0x20||o==0x21||o==0x30||o==0x31;bool gone=false;if(candidate){L x=key(g),p=barrier;for(int j=0;j<a.nr;j++)p=max(p,ww[a.r[j]]);for(int j=0;j<a.nw;j++)p=max(p,rr[a.w[j]]);auto it=last.find(x);if(it!=last.end()&&it->second>p&&!del[it->second-1]){del[i]=del[it->second-1]=true;hist[o]+=2;last.erase(it);gone=true;}if(!gone)last[x]=k;}if(!gone){for(int j=0;j<a.nr;j++)rr[a.r[j]]=k;for(int j=0;j<a.nw;j++)ww[a.w[j]]=k;}}
r.reset();Writer w(r,r.B);for(L i=0;i<r.counts[0];i++){Gate g=r.read(i);if(!del[i])w.put(g);}for(auto[k,v]:hist)cerr<<hex<<k<<dec<<" "<<v<<"\n";cerr<<"out_ops "<<w.ops.size()<<" paid "<<w.a[2].size()<<endl;w.write(argv[2]);}
