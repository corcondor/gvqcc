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


int AND(int x,int y){return x==0||y==0?0:x==1&&y==1?1:2;}
int XOR(int x,int y){return x==2||y==2?2:x^y;}
int JOIN(int old,int v,int c){return c==0?old:c==1?v:old==v?old:2;}
struct Change{U i;uint8_t old;U stamp;};
struct Frame{U id;vector<Change> edits;};
int main(int argc,char**argv){
 assert(argc==3);Reader r(argv[1]);Writer w(r,r.B);
 vector<uint8_t> val(r.Q+r.B,2);fill(val.begin(),val.begin()+r.Q,0);
 for(auto p:r.regs){U nl,nr;memcpy(&nl,p.ptr,4);memcpy(&nr,p.ptr+4,4);for(U i=0;i<nr;i++){U x;memcpy(&x,p.ptr+8+nl+4*i,4);if(x>>31)val[x&0x1fffffff]=2;}}
 vector<U> stamp(val.size(),0);vector<Frame> frames;U serial=0;
 auto set=[&](U i,int x){assert(i<val.size());if(val[i]==x)return;if(!frames.empty()&&stamp[i]!=frames.back().id){frames.back().edits.push_back({i,val[i],stamp[i]});stamp[i]=frames.back().id;}val[i]=x;};
 auto test=[&](U id){U i=r.Q+(id&0x7fffffff);assert(i<val.size());int v=val[i];return (id>>31)&&v!=2?v^1:v;};
 auto update=[&](U i,int v,int c){set(i,JOIN(val[i],v,c));};
 vector<int> scopes{1}; // 0: inactive; 1: known active; 2: speculative active, merge on pop
 L removed[128]={},lowered[128]={},unknownScopes=0;L keptHMR=0;
 for(L i=0;i<r.counts[0];i++){
  Gate g=r.read(i);int op=g.op&127;U a=g.a,b=g.b,d=g.t;int flag=g.op&128;
  if(g.op==129){
   int c=scopes.back()==0?0:test(g.cond);scopes.push_back(c);w.put(g);
   if(c==2){frames.push_back({++serial,{}});unknownScopes++;set(r.Q+(g.cond&0x7fffffff),g.cond>>31?0:1);}
   continue;
  }
  if(op==1){assert(scopes.size()>1);int mode=scopes.back();scopes.pop_back();if(mode==2){auto f=std::move(frames.back());frames.pop_back();for(auto it=f.edits.rbegin();it!=f.edits.rend();++it){int v=val[it->i];val[it->i]=it->old;stamp[it->i]=it->stamp;set(it->i,JOIN(it->old,v,2));}}w.put(g);continue;}
  int c=scopes.back()==0?0:flag?test(g.cond):1;
  bool drop=false;int n=op;
  if(c==0 && op!=0x50 && op!=0x12 && op!=6 && op!=7 && op!=0){drop=true;}
  else switch(op){
  case 0x11:update(a,XOR(val[a],1),c);break;
  case 0x12:update(a,0,c);break;
  case 0x10:if(val[a]==0)drop=true;break;
  case 0x21:if(val[a]==0)drop=true;else if(val[a]==1){g.a=b;n=0x11;}update(b,XOR(val[b],val[a]),c);break;
  case 0x20:if(val[a]==0||val[b]==0)drop=true;else if(val[a]==1&&val[b]!=1){g.a=b;n=0x10;}else if(val[b]==1&&val[a]!=1)n=0x10;break;
  case 0x22:{int x=val[a],y=val[b];if(x==y&&x!=2)drop=true;update(a,y,c);update(b,x,c);break;}
  case 0x31:{int x=val[a],y=val[b],z=AND(x,y);if(z==0)drop=true;else if(z==1){n=0x11;g.a=d;}else if(x==1||y==1){n=0x21;g.a=x==1?b:a;g.b=d;}update(d,XOR(val[d],z),c);break;}
  case 0x30:{int x=val[a],y=val[b],z=val[d];if(x==0||y==0||z==0)drop=true;else {vector<U> u;for(U q:{a,b,d})if(val[q]!=1)u.push_back(q);if(u.size()==1){n=0x10;g.a=u[0];}else if(u.size()==2){n=0x20;g.a=u[0];g.b=u[1];}}break;}
  case 0x32:{int k=val[a],x=val[b],y=val[d];if(k==0||(x==y&&x!=2))drop=true;else if(k==1){n=0x22;g.a=b;g.b=d;}int kc=AND(c,k);update(b,y,kc);update(d,x,kc);break;}
  case 0x50:keptHMR++;update(a,0,c);update(r.Q+g.bit,2,c);break;
  case 0x40:case 0x41:{U j=r.Q+g.bit;int v=op&1;if(val[j]==v)drop=true;update(j,v,c);break;}
  case 0x42:{U j=r.Q+g.bit;int v=val[j];if(flag&&(g.cond&0x7fffffff)==g.bit&&c==2){set(j,g.cond>>31?1:0);}else update(j,XOR(v,1),c);break;}
  case 0:case 6:case 7:break;
  default:cerr<<"unsupported "<<op<<" at "<<i<<endl;return 2;
  }
  if(drop){removed[op]++;continue;}
  if(n!=op){lowered[op]++;g.op=flag|n;}
  w.put(g);
 }
 assert(scopes.size()==1&&frames.empty());
 w.write(argv[2]);cerr<<"ops "<<w.ops.size()<<" static_paid "<<w.a[2].size()<<" scopes "<<unknownScopes<<" HMR "<<keptHMR<<endl;
 for(int i=0;i<128;i++)if(removed[i]||lowered[i])cerr<<"opcode "<<i<<" removed "<<removed[i]<<" lowered "<<lowered[i]<<endl;
}

