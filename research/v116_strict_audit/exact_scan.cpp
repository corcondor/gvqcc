#include <cstdint>
#include <vector>
#include <unordered_map>
#include <fstream>
#include <algorithm>
#include <iostream>
using U=uint32_t;using I=int64_t;using K=uint64_t;
extern "C" void scan(const uint8_t* ops,I n,const U* a3,const U* b3,const U* c3,const U* a2,const U* b2,const U* a1,const U* bt,const U* cd,int Q,int B,I n1,I n2,I n3,I nb,I nc,uint8_t* del,const char* out){
 std::vector<I> rd(Q,-1),wr(Q,-1),bw(B,-1);std::unordered_map<K,I> last;last.reserve(1200000);
 I j1=0,j2=0,j3=0,jb=0,jc=0,pairs=0,paidpairs=0;int depth=0;
 for(I i=0;i<n;i++){
  unsigned o=ops[i],v=o&127,k=(o&48)>>4;int a=-1,b=-1,c=-1,bit=-1,guard=-1;
  if(k==1)a=a1[j1++];else if(k==2){a=a2[j2];b=b2[j2++];}else if(k==3){a=a3[j3];b=b3[j3];c=c3[j3++];}
  if((o&64)&&v!=6&&v!=7)bit=bt[jb++]; if(o&128)guard=cd[jc++];
  if(o==129){depth++;continue;}if(o==1){depth--;continue;}
  bool x=v==17||v==33||v==49,p=v==16||v==32||v==48;
  if(depth==0&&(x||p)){
   int x0=a,x1=b,x2=c;if(v==49&&x0>x1)std::swap(x0,x1);if(p){if(k==2&&x0>x1)std::swap(x0,x1);if(k==3){if(x0>x1)std::swap(x0,x1);if(x1>x2)std::swap(x1,x2);if(x0>x1)std::swap(x0,x1);}}
   K key=(K)o|((K)(x0+1)<<8)|((K)(x1+1)<<18)|((K)(x2+1)<<28)|((K)(guard+1)<<38);
   auto it=last.find(key);bool good=false;
   if(it!=last.end()){
    I prev=it->second;good=(guard<0||bw[guard]<prev);
    if(x){int t=k==1?a:k==2?b:c;good &= rd[t]<prev;if(k>1)good &= wr[a]<prev;if(k>2)good &= wr[b]<prev;}
    else{good &= wr[a]<prev;if(k>1)good &= wr[b]<prev;if(k>2)good &= wr[c]<prev;}
    if(good){del[i]=del[prev]=1;last.erase(it);pairs++;paidpairs+=(k==3);}
   }
   if(!good)last[key]=i;
  }
  if(x){if(k==1)wr[a]=i;else if(k==2){rd[a]=i;wr[b]=i;}else{rd[a]=rd[b]=i;wr[c]=i;}}
  else if(p){if(k>=1)rd[a]=i;if(k>=2)rd[b]=i;if(k>=3)rd[c]=i;}
  else {if(k>=1)rd[a]=wr[a]=i;if(k>=2)rd[b]=wr[b]=i;if(k>=3)rd[c]=wr[c]=i;}
  if(bit>=0)bw[bit]=i;
 }
 if(j1!=n1||j2!=n2||j3!=n3||jb!=nb||jc!=nc||depth!=0)std::abort();
 std::cerr<<"cancelled pairs "<<pairs<<" paid pairs "<<paidpairs<<"\n";
 std::fill(wr.begin(),wr.end(),n);std::vector<I> barrier(Q,n);std::vector<int> measure(Q,-1);
 std::ofstream f(out);I dead=0;depth=0;
 for(I i=n;i-->0;){
  unsigned o=ops[i],v=o&127,k=(o&48)>>4;int a=-1,b=-1,c=-1,bit=-1,guard=-1;
  if(k==1)a=a1[--j1];else if(k==2){--j2;a=a2[j2];b=b2[j2];}else if(k==3){--j3;a=a3[j3];b=b3[j3];c=c3[j3];}
  if((o&64)&&v!=6&&v!=7)bit=bt[--jb];if(o&128)guard=cd[--jc];
  if(o==1){depth++;continue;}if(o==129){depth--;continue;}if(del[i])continue;
  if(o==49&&depth==0&&measure[c]>=0&&wr[a]>barrier[c]&&wr[b]>barrier[c]){
   del[i]=2;f<<i<<" "<<barrier[c]<<" "<<a<<" "<<b<<" "<<measure[c]<<"\n";dead++;
  }
  bool x=v==17||v==33||v==49,p=v==16||v==32||v==48;
  auto read=[&](int w){barrier[w]=i;measure[w]=-1;};
  if(x){if(k==1)wr[a]=i;else if(k==2){read(a);wr[b]=i;}else{read(a);read(b);wr[c]=i;}}
  else if(p){if(k>=1)read(a);if(k>=2)read(b);if(k>=3)read(c);}
  else{if(k>=1){read(a);wr[a]=i;}if(k>=2){read(b);wr[b]=i;}if(k>=3){read(c);wr[c]=i;}if(o==80&&depth==0)measure[a]=bit;}
 }
 if(j1||j2||j3||jb||jc||depth)std::abort();
 std::cerr<<"dead write sites "<<dead<<"\n";
}
