#include <stdexcept>
// Exact affine-symbolic Boolean transport. Fresh independent atoms are
// an overapproximation; product interning uses FULL bitset equality,
// never a hash match as proof. Rebase preserves the live linear span.
// Input ABI: named syndrome bits arbitrary; all other quantum bits zero.
#include "native.hpp"
#include <bitset>
#include <memory>
using V=bitset<4096>;
V unit(U i){V v;v.set(i);return v;}
const V ONE=unit(0);
struct Key{V a,b;bool operator==(Key const&k)const{return (a==k.a&&b==k.b)||(a==k.b&&b==k.a);}};
struct KH{size_t operator()(Key const&k)const{size_t a=hash<V>{}(k.a),b=hash<V>{}(k.b);return a+b+((a^b)*0x9e3779b97f4a7c15ULL);}};
struct Change{U q;V old;U stamp;};
struct Frame{U id;vector<Change> changed;};
int main(int argc,char**argv){
 assert(argc==3);Reader r(argv[1]);assert(r.Q==900);vector<V> q(r.Q);
 U next=1,serial=0;vector<U> stamp(r.Q);vector<Frame> frames;
 unordered_map<Key,U,KH> products;unordered_map<U,U> classical;map<U,Key> revprod;
 L rebases=0,found=0,phase=0,cleanup=0,saved=0,swap_saved=0;map<string,L> hist;
 auto fresh=[&](){assert(next<4096);return unit(next++);};
 for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);if(p.ptr[8]=='S'){for(U j=0;j<l;j++){U x;memcpy(&x,p.ptr+8+n+4*j,4);x&=0x7fffffff;assert(x<r.Q);q[x]=fresh();}}}
 assert(next==841);
 bool merging=false;auto prod=[&](V a,V b)->V{
  bool ca=a[0],cb=b[0];a.reset(0);b.reset(0);V z;
  if(a.any()&&b.any()){
   if(a==b)z=a;else{
    auto atom=[&](V const&x,V const&y){Key k{x,y};auto it=products.find(k);U i;if(it!=products.end())i=it->second;else{i=next++;assert(i<4096);revprod.emplace(i,k);products.emplace(move(k),i);}return i;};
    if(a.count()*b.count()<=64 && next+128<3000 && !merging){
     vector<U> A,B;for(U j=1;j<next;j++){if(a[j])A.push_back(j);if(b[j])B.push_back(j);}
     for(U i:A)for(U j:B)z.flip(i==j?i:atom(unit(i),unit(j)));
    }else z.set(atom(a,b));
   }
  }
  if(ca)z^=b;if(cb)z^=a;if(ca&&cb)z.flip(0);return z;
 };
 auto cond=[&](U id){U b=id&0x7fffffff;auto it=classical.find(b);U i;if(it==classical.end()){i=next++;assert(i<4096);classical[b]=i;}else i=it->second;V z=unit(i);if(id>>31)z.flip(0);return z;};
 auto set=[&](U i,V const&v){if(q[i]==v)return;if(!frames.empty()&&stamp[i]!=frames.back().id){frames.back().changed.push_back({i,q[i],stamp[i]});stamp[i]=frames.back().id;}q[i]=v;};
 static_assert(sizeof(V)==512);
 auto top=[](V const&x){array<uint64_t,64> z;memcpy(z.data(),&x,sizeof(x));for(int j=63;j>=0;j--)if(z[j])return U(j*64+63-__builtin_clzll(z[j]));return U(0);};
 for(U j=1;j<4096;j++)assert(top(unit(j))==j);
 auto rebase=[&](){
  // Express all currently live rows and saved scope rows in a fresh
  // independent basis of their linear span. Each old residual is a
  // function of the original Boolean inputs, so forgetting dependencies
  // among residuals can only weaken, never invent, equalities.
  vector<V> piv(4096);vector<U> ids(4096);U n=1;
  auto cv=[&](V x){V y;if(x[0])y.set(0);x.reset(0);while(x.any()){
    U k=top(x);
    assert(k);if(!ids[k]){ids[k]=n++;piv[k]=x;}y.flip(ids[k]);x^=piv[k];
   }return y;};
  for(V&v:q)v=cv(v);for(auto&f:frames)for(auto&c:f.changed)c.old=cv(c.old);
  assert(n<2800);next=n;products.clear();revprod.clear();classical.clear();rebases++;
 };

 // Exact HMR phase-only lifetime normalization, with affine and quadratic
 // witnesses on other live wires. No input-dependent host branch.
 struct Epoch{L at;U bit,wire,scope;vector<Gate> repay;bool ok=true;vector<L> uses;};
 vector<Epoch> ep;vector<int> owner(r.B,-1);vector<bool> publicbit(r.B);
 for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);if(p.ptr[8]=='E')for(U j=0;j<l;j++){U x;memcpy(&x,p.ptr+8+n+4*j,4);publicbit.at(x&0x7fffffff)=true;}}
 auto invalidate=[&](U id){id&=0x7fffffff;if(id<r.B&&owner[id]>=0)ep[owner[id]].ok=false;};
 auto scope_id=[&]()->U{return frames.empty()?0:frames.back().id;};
 auto live_scope=[&](U id){if(id==0)return true;for(auto const&f:frames)if(f.id==id)return true;return false;};
 auto close=[&](U id){if(owner.at(id)>=0){auto &e=ep[owner[id]];if(scope_id()==0||scope_id()==e.scope)owner[id]=-1;else e.ok=false;}};
 using R=bitset<901>; // bit 900 represents constant one
 auto certificate=[&](U a,U mb,vector<Gate>& repay,bool use_elim)->bool{
   V target=q[a];
   auto direct=[&](V x,R &out)->bool{
     if(x[0]){out.flip(900);x.reset(0);}if(x.none())return true;
     for(U j=0;j<r.Q;j++)if(j!=a){
       V y=q[j];bool k=y[0];y.reset(0);if(y==x){out.flip(j);if(k)out.flip(900);return true;}
     }return false;
   };
   auto linphase=[&](R const& z){if(z[900])repay.push_back(Gate{128,0,0,0,0,mb});for(U j=0;j<r.Q;j++)if(z[j])repay.push_back(Gate{144,j,0,0,0,mb});};
   R lin;
   if(direct(target,lin)){linphase(lin);return true;}
   // Test whether the exact affine span of the remaining bank contains
   // target. Only invoke this on the early extraction where known
   // structural singularities arise. Rebase is conservative.
   vector<V> piv;vector<R> coeff;vector<int> have;
   auto init=[&](){
    piv.resize(4096);coeff.resize(4096);have.assign(4096,0);
    for(U j=0;j<r.Q;j++)if(j!=a){V v=q[j];R z;z.set(j);if(v[0]){z.flip(900);v.reset(0);}
     while(v.any()){U k=top(v);if(!have[k]){piv[k]=v;coeff[k]=z;have[k]=1;break;}v^=piv[k];z^=coeff[k];}
    }
   };
   auto solve=[&](V v,R &z)->bool{
    R d;if(direct(v,d)){z=d;return true;}
    if(!use_elim)return false;
    if(have.empty())init();z.reset();if(v[0]){z.set(900);v.reset(0);}
    while(v.any()){U k=top(v);if(!have[k])return false;v^=piv[k];z^=coeff[k];}return true;
   };
   if(solve(target,lin)){linphase(lin);return true;}
   // A general quadratic polynomial in the current affine live bank:
   // expand exactly one interned product layer, with full bitset proof.
   // If any factor cannot be expressed, leave that epoch unchanged.
   if(target.count()>24)return false;
   map<pair<U,U>,bool> phase;
   R sum;
   for(U k=0;k<next;k++)if(target[k]){
     R z;if(solve(unit(k),z)){sum^=z;continue;}
     auto it=revprod.find(k);if(it==revprod.end())return false;
     R x,y;if(!solve(it->second.a,x)||!solve(it->second.b,y))return false;
     if(x.count()*y.count()>512)return false;
     for(U i=0;i<=900;i++)if(x[i])for(U j=0;j<=900;j++)if(y[j]){
       if(i==900||j==900||i==j)sum.flip(min(i,j));else{auto p=minmax(i,j);phase[{p.first,p.second}]=!phase[{p.first,p.second}];}
     }
   }
   linphase(sum);for(auto const&[p,v]:phase)if(v)repay.push_back(Gate{160,p.first,p.second,0,0,mb});
   if(repay.size()>256)return false;
   return true;
 };
 L hmrs=0,proved=0,proved0=0;
 for(L i=0;i<r.counts[0];i++){
  if(next>2800)rebase();
  Gate g=r.read(i);int op=g.op&127,flag=g.op&128;U a=g.a,b=g.b,t=g.t;
  if(flag){
   U bit=g.cond&0x7fffffff;
   if(bit<r.B&&owner[bit]>=0){
    auto &e=ep[owner[bit]];
    if(live_scope(e.scope)&&(op==0||op==16||op==32||op==48))e.uses.push_back(i);
    else e.ok=false;
   }
  }
  if(g.op==129){frames.push_back({++serial,{}});continue;}
  if(op==1){assert(!frames.empty());merging=true;auto f=move(frames.back());frames.pop_back();V k=f.changed.empty()?V{}:fresh();for(auto&c:f.changed){V delta=q[c.q]^c.old;q[c.q]=c.old;stamp[c.q]=c.stamp;if(delta.any())set(c.q,c.old^prod(delta,k));}merging=false;classical.clear();continue;}
  if(op==64||op==65||op==66){if(op==66||flag)invalidate(g.bit);else close(g.bit);classical.erase(g.bit);continue;}
  if(op==80){
   hmrs++;if(flag)invalidate(g.bit);else{close(g.bit);if(owner[g.bit]<0&&!publicbit.at(g.bit)){
      vector<Gate> rep;
      // Full affine span during the first 1800 HMRs; cheap certificates elsewhere.
      if(certificate(a,g.bit,rep,hmrs<=1800)){owner[g.bit]=int(ep.size());ep.push_back({i,g.bit,a,scope_id(),rep,true,{}});proved++;if(rep.empty())proved0++;}
   }}
   classical.erase(g.bit);
  }
  if(op==0||op==6||op==7)continue;
  V k=flag?cond(g.cond):ONE;
  auto update=[&](U x,V delta){if(delta.any())set(x,q[x]^prod(delta,k));};
  switch(op){
   case 17:update(a,ONE);break;
   case 18:case 80:update(a,q[a]);break;
   case 33:update(b,q[a]);break;
   case 34:{V delta=q[a]^q[b];update(a,delta);update(b,delta);break;}
   case 16:case 32:case 48:break;
   case 49:update(t,prod(q[a],q[b]));break;
   case 50:{V p=prod(q[a],q[b]^q[t]);update(b,p);update(t,p);break;}
   default:cerr<<"unsupported "<<op<<" at "<<i<<endl;return 2;
  }
  if(i%5000000==0)cerr<<"scan "<<i<<" hmr "<<hmrs<<" certified "<<proved<<endl;
 }
 assert(frames.empty());
 map<L,size_t> begin;std::set<L> uses;L n=0,zeros=0,paid=0;ofstream log(string(argv[2])+".epochs.tsv");
 for(size_t j=0;j<ep.size();j++){auto&e=ep[j];if(!e.ok||e.uses.empty())continue;
   // Preserve original m=0 phase baseline. To avoid command inflation,
   // accept only when new repayment <= the number of original uses.
   if(e.repay.size()>e.uses.size())continue;
   begin[e.at]=j;for(L i:e.uses)if(!uses.insert(i).second)throw std::runtime_error("overlapping epoch");n++;zeros+=e.repay.empty();
   log<<e.at<<' '<<e.wire<<' '<<e.bit<<" repay "<<e.repay.size()<<" uses "<<e.uses.size()<<'\n';
 }
 r.reset();Writer w(r,r.B);L rem=0,add=0;
 for(L i=0;i<r.counts[0];i++){
  auto g=r.read(i);if(uses.count(i)){
    if(g.cond>>31){g.op&=127;w.put(g);}else{rem++;paid+=((g.op&127)==48);}continue;
  }
  w.put(g);auto it=begin.find(i);if(it!=begin.end())for(auto h:ep[it->second].repay){w.put(h);add++;}
 }
 w.write(argv[2]);cerr<<"hmrs "<<hmrs<<" symbolic "<<proved<<" zero "<<proved0<<" eligible "<<n<<" zero_eligible "<<zeros<<" removed "<<rem<<" added "<<add<<" paid_removed "<<paid<<" Q "<<r.Q<<" ops "<<w.ops.size()<<" paid "<<w.a[2].size()<<endl;
}

