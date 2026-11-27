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

int commute(const char*src,const char*dst){
 Reader r(src);vector<uint8_t> del(r.counts[0]);vector<int64_t> rd(r.Q,-1),wr(r.Q,-1),bw(r.B,-1);unordered_map<uint64_t,int64_t> last;last.reserve(1200000);int depth=0;L pairs=0;
 for(L i=0;i<r.counts[0];i++){Gate g=r.read(i);int o=g.op,v=o&127,k=(o&48)>>4;int a=k>=1?g.a:-1,b=k>=2?g.b:-1,c=k==3?g.t:-1,bit=((o&64)&&v!=6&&v!=7)?g.bit:-1,guard=(o&128)?g.cond:-1;
 if(o==129){depth++;continue;}if(o==1){depth--;continue;}
 bool x=v==17||v==33||v==49,p=v==16||v==32||v==48;
 if(depth==0&&(x||p)){
 int x0=a,x1=b,x2=c;if(v==49&&x0>x1)swap(x0,x1);if(p){if(k==2&&x0>x1)swap(x0,x1);if(k==3){if(x0>x1)swap(x0,x1);if(x1>x2)swap(x1,x2);if(x0>x1)swap(x0,x1);}}
 uint64_t key=(uint64_t)o|((uint64_t)(x0+1)<<8)|((uint64_t)(x1+1)<<18)|((uint64_t)(x2+1)<<28)|((uint64_t)(guard+1)<<38);auto it=last.find(key);bool good=false;
 if(it!=last.end()){auto prev=it->second;good=guard<0||bw[guard]<prev;if(x){int t=k==1?a:k==2?b:c;good &= rd[t]<prev;if(k>1)good &= wr[a]<prev;if(k>2)good &= wr[b]<prev;}else{good &= wr[a]<prev;if(k>1)good &= wr[b]<prev;if(k>2)good &= wr[c]<prev;}if(good){del[i]=del[prev]=1;last.erase(it);pairs++;}}
 if(!good)last[key]=i;}
 if(x){if(k==1)wr[a]=i;else if(k==2){rd[a]=i;wr[b]=i;}else{rd[a]=rd[b]=i;wr[c]=i;}}
 else if(p){if(k>=1)rd[a]=i;if(k>=2)rd[b]=i;if(k>=3)rd[c]=i;}
 else{if(k>=1)rd[a]=wr[a]=i;if(k>=2)rd[b]=wr[b]=i;if(k>=3)rd[c]=wr[c]=i;}
 if(bit>=0)bw[bit]=i;
 }
 assert(depth==0);r.reset();Writer w(r,r.B);for(L i=0;i<r.counts[0];i++){Gate g=r.read(i);if(!del[i])w.put(g);}w.write(dst);cerr<<"pairs "<<pairs<<" ops "<<w.ops.size()<<" paid "<<w.a[2].size()<<endl;return 0;
}
int and3(int a,int b){return a==0||b==0?0:a==1&&b==1?1:2;}int xor3(int a,int b){return a==2||b==2?2:a^b;}int join(int old,int v,int c){return c==0?old:c==1?v:old==v?old:2;}
int dropdead(int argc,char**argv){assert(argc==4);Reader r(argv[1]);vector<int> q(r.Q,0),b(r.B,2),stack{1};for(auto p:r.regs){U nl,nr;memcpy(&nl,p.ptr,4);memcpy(&nr,p.ptr+4,4);for(U i=0;i<nr;i++){U x;memcpy(&x,p.ptr+8+nl+4*i,4);if(x>>31)q[x&0x1fffffff]=2;}}Writer w(r,r.B);L ccx=0,ccz=0,cswap=0;ofstream log(argv[3]);
 for(L i=0;i<r.counts[0];i++){Gate g=r.read(i);int op=g.op&127;U a=g.a,d=g.b,t=g.t;auto test=[&](U id){int v=b[id&0x7fffffff];if(id>>31&&v!=2)v^=1;return v;};if(g.op==129){stack.push_back(and3(stack.back(),test(g.cond)));w.put(g);continue;}if(op==1){assert(stack.size()>1);stack.pop_back();w.put(g);continue;}int c=(g.op&128)?and3(stack.back(),test(g.cond)):stack.back();bool drop=false;
 switch(op){case 0x11:q[a]=xor3(q[a],c);break;case 0x12:q[a]=join(q[a],0,c);break;case 0x21:q[d]=xor3(q[d],and3(c,q[a]));break;case 0x22:{int x=q[a],y=q[d];q[a]=join(x,y,c);q[d]=join(y,x,c);break;}case 0x31:{int z=and3(c,and3(q[a],q[d]));if(z==0){drop=true;ccx++;}q[t]=xor3(q[t],z);break;}case 0x30:if(and3(c,and3(q[a],and3(q[d],q[t])))==0){drop=true;ccz++;}break;case 0x32:{int k=and3(c,q[a]),x=q[d],y=q[t];if(k==0||(x==y&&x!=2)){drop=true;cswap++;}q[d]=join(x,y,k);q[t]=join(y,x,k);break;}case 0x50:q[a]=join(q[a],0,c);b[g.bit]=join(b[g.bit],2,c);break;case 0x40:b[g.bit]=join(b[g.bit],0,c);break;case 0x41:b[g.bit]=join(b[g.bit],1,c);break;case 0x42:b[g.bit]=xor3(b[g.bit],c);break;case 0:case 6:case 0x10:case 0x20:break;default:cerr<<"unsupported "<<op<<" at "<<i<<endl;return 2;}
 if(drop){log<<i<<'\t'<<op<<'\t'<<a<<'\t'<<d<<'\t'<<t<<'\t'<<c<<'\n';}else w.put(g);
 }
 assert(stack.size()==1);w.write(argv[2]);cerr<<"removed CCX "<<ccx<<" CCZ "<<ccz<<" CSWAP "<<cswap<<" paid "<<w.a[2].size()<<" ops "<<w.ops.size()<<endl;return 0;
}
int main(int argc,char**argv){assert(argc==5);commute(argv[1],argv[2]);char*args[]={argv[0],argv[2],argv[3],argv[4]};return dropdead(4,args);}
