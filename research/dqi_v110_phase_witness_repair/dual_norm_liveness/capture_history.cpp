#include "native.hpp"
#include <random>
#include <immintrin.h>
using V=uint64_t __attribute__((vector_size(64)));
inline L pop(V v){__m512i x=_mm512_popcnt_epi64((__m512i)v);return _mm512_reduce_add_epi64(x);}
int main(int argc,char**argv){
assert(argc==6);
set<L> wanted;
ifstream ix(argv[4]);
for(L n;ix>>n;)wanted.insert(n);
ofstream cap(argv[5],ios::binary);
Reader r(argv[1]);ifstream in(argv[2],ios::binary);ofstream out(argv[3]);U nb=0;in.read((char*)&nb,4);vector<U>S(840),E(49140);vector<bool>qs(r.Q);for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);string name(p.ptr+8,n);U j=stoul(name.substr(1));for(U k=0;k<12;k++){U v;memcpy(&v,p.ptr+8+n+4*k,4);v&=0x7fffffff;if(name[0]=='S'){S[12*j+k]=v;qs[v]=true;}else if(name[0]=='E')E[12*j+k]=v;else abort();}}
vector<V>q(r.Q),b(r.B),x(840),y(49140),stack;stack.reserve(128);V all;memset(&all,255,64);out<<"batch,n,paid,value,phase,dirty,mask,union,official_value,official_phase\n";
for(U shot=0;shot<nb;shot++){U batchid;L seed;V want;in.read((char*)&batchid,4);in.read((char*)&seed,8);in.read((char*)x.data(),64*x.size());in.read((char*)y.data(),64*y.size());in.read((char*)&want,64);assert(in);mt19937_64 rng(seed);fill(q.begin(),q.end(),V{});fill(b.begin(),b.end(),V{});for(U j=0;j<S.size();j++)q[S[j]]=x[j];for(U j=0;j<E.size();j++)b[E[j]]=y[j];r.reset();stack={all};V phase{};L paid=0;
auto site=wanted.begin();
for(L i=0;i<r.counts[0];i++){
if(site!=wanted.end()&&i==*site){cap.write((char*)q.data(),64*r.Q);cap.write((char*)&stack.back(),64);++site;}
auto g=r.read(i);int op=g.op&127;if(g.op==129){stack.push_back(stack.back()&((g.cond>>31)?~b[g.cond&0x7fffffff]:b[g.cond&0x7fffffff]));continue;}if(op==1){stack.pop_back();continue;}V k=stack.back();if(g.op&128)k&=((g.cond>>31)?~b[g.cond&0x7fffffff]:b[g.cond&0x7fffffff]);U a=g.a,d=g.b,t=g.t;V delta;if((op&0x30)==0x30)paid+=pop(k);switch(op){case 0x11:q[a]^=k;break;case 0x12:q[a]&=~k;break;case 0x21:q[d]^=k&q[a];break;case 0x22:delta=k&(q[a]^q[d]);q[a]^=delta;q[d]^=delta;break;case 0x31:q[t]^=k&q[a]&q[d];break;case 0x32:delta=k&q[a]&(q[d]^q[t]);q[d]^=delta;q[t]^=delta;break;case 0x50:{V m;for(int j=0;j<8;j++)m[j]=rng();phase^=k&m&q[a];b[g.bit]=(b[g.bit]&~k)|(m&k);q[a]&=~k;break;}case 0x40:b[g.bit]&=~k;break;case 0x41:b[g.bit]|=k;break;case 0x42:b[g.bit]^=k;break;case 0:phase^=k;break;case 0x10:phase^=k&q[a];break;case 0x20:phase^=k&q[a]&q[d];break;case 0x30:phase^=k&q[a]&q[d]&q[t];break;default:cerr<<"bad "<<op<<endl;return 3;}}assert(site==wanted.end());
V er{},dirty{},mb{};for(U j=0;j<S.size();j++)er|=q[S[j]]^x[j];for(U j=0;j<r.Q;j++)if(!qs[j])dirty|=q[j];for(U j=0;j<E.size();j++)mb|=b[E[j]]^y[j];V pe=phase^want,ve=er|dirty;out<<batchid<<",512,"<<paid<<','<<pop(er)<<','<<pop(pe)<<','<<pop(dirty)<<','<<pop(mb)<<','<<pop(er|pe|dirty|mb)<<','<<pop(ve)<<','<<pop(pe&~ve)<<'\n';out.flush();cerr<<"batch "<<batchid<<" value="<<pop(er)<<" phase="<<pop(pe)<<" dirty="<<pop(dirty)<<" mask="<<pop(mb)<<" paid="<<double(paid)/512<<endl;}assert(in);}
