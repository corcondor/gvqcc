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
 assert(argc==4);bool allow_hmr=stoi(argv[3]);Reader r(argv[1]);assert(r.Q==900);Writer w(r,r.B+allow_hmr);vector<V> q(r.Q);
 U next=1,serial=0;vector<U> stamp(r.Q);vector<Frame> frames;
 unordered_map<Key,U,KH> products;unordered_map<U,U> classical;
 L rebases=0,found=0,phase=0,cleanup=0,saved=0,swap_saved=0;map<string,L> hist;
 auto fresh=[&](){assert(next<4096);return unit(next++);};
 for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);if(p.ptr[8]=='S'){for(U j=0;j<l;j++){U x;memcpy(&x,p.ptr+8+n+4*j,4);x&=0x7fffffff;assert(x<r.Q);q[x]=fresh();}}}
 assert(next==841);
 bool merging=false;auto prod=[&](V a,V b)->V{
  bool ca=a[0],cb=b[0];a.reset(0);b.reset(0);V z;
  if(a.any()&&b.any()){
   if(a==b)z=a;else{
    auto atom=[&](V const&x,V const&y){Key k{x,y};auto it=products.find(k);U i;if(it!=products.end())i=it->second;else{i=next++;assert(i<4096);products.emplace(move(k),i);}return i;};
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
  assert(n<2800);next=n;products.clear();classical.clear();rebases++;
 };
 // Direct linear witnesses; exact comparison of all coordinates.
 auto witness=[&](V const&p,U skip1,U skip2)->pair<U,bool>{
   if(p.none()||p==ONE)return {r.Q,false};
   for(U i=0;i<r.Q;i++)if(i!=skip1&&i!=skip2&&q[i]==p)return {i,false};
   V p1=p^ONE;
   for(U i=0;i<r.Q;i++)if(i!=skip1&&i!=skip2&&q[i]==p1)return {i,true};
   return {r.Q,false};
 };
 ofstream edits(string(argv[2])+".edits.tsv");
 auto log=[&](L i,string tag){hist[tag]++;edits<<i<<"\t"<<tag<<"\n";};
 for(L i=0;i<r.counts[0];i++){
  if(next>2800)rebase();
  Gate g=r.read(i);int op=g.op&127,flag=g.op&128;U a=g.a,b=g.b,t=g.t;
  if(g.op==129){frames.push_back({++serial,{}});w.put(g);continue;}
  if(op==1){
   assert(!frames.empty());
   // Use a shared unknown selector for this exact scope. Scope snapshots
   // are in the same symbol frame and no rebase occurs within the merge.
   merging=true;auto f=move(frames.back());frames.pop_back();V k=f.changed.empty()?V{}:fresh();
   for(auto&c:f.changed){V delta=q[c.q]^c.old;q[c.q]=c.old;stamp[c.q]=c.stamp;if(delta.any())set(c.q,c.old^prod(delta,k));}
   merging=false;classical.clear();w.put(g);continue;
  }
  if(op==64||op==65||op==66){classical.erase(g.bit);w.put(g);continue;}
  if(op==80){classical.erase(g.bit);}
  if(op==0||op==6||op==7){w.put(g);continue;}
  V k=flag?cond(g.cond):ONE;
  auto gate=[&](int o,U x=0,U y=0,U z=0){w.put(Gate{(unsigned char)(o|flag),x,y,z,0,g.cond});};
  auto update=[&](U x,V delta){if(delta.any())set(x,q[x]^prod(delta,k));};
  switch(op){
   case 17: update(a,ONE);w.put(g);break;
   case 18:case 80: update(a,q[a]);w.put(g);break;
   case 33: update(b,q[a]);w.put(g);break;
   case 34:{V delta=q[a]^q[b];update(a,delta);update(b,delta);w.put(g);break;}
   case 16:case 32:w.put(g);break;
   case 49:{
    V p=prod(q[a],q[b]);bool done=true;
    if(p.none()){log(i,"ccx_zero");}
    else if(p==ONE){gate(17,t);log(i,"ccx_one");}
    else if(allow_hmr&&p==q[t]){
     // Only replace when pre-measurement target EXACTLY equals the product.
     // Scope and original condition are unchanged; private result is
     // never consumed by the original tape and is cleared immediately.
     if(flag)w.put(Gate{129,0,0,0,0,g.cond});
     w.put(Gate{80,t,0,0,r.B,0});w.put(Gate{160,a,b,0,0,r.B});
     w.put(Gate{64,0,0,0,r.B,0});if(flag)w.put(Gate{1});
     log(i,"ccx_exact_hmr");cleanup++;
    }else{
     auto [x,flip]=witness(p,t,r.Q);
     if(x<r.Q){if(flip)gate(17,t);gate(33,x,t);log(i,"ccx_linear");found++;}
     else done=false;
    }
    update(t,p);if(!done)w.put(g);else saved++;break;
   }
   case 48:{
    bool done=false;U u[3]={a,b,t};
    for(U j=0;j<3&&!done;j++){
     U x=u[(j+1)%3],y=u[(j+2)%3],z=u[j];V p=prod(q[x],q[y]);
     if(p.none()){log(i,"ccz_zero");done=true;}
     else if(p==ONE){gate(16,z);log(i,"ccz_one");done=true;}
     else if(p==q[z]){gate(16,z);log(i,"ccz_square");done=true;}
     else if(p==(q[z]^ONE)){log(i,"ccz_complement");done=true;}
     else{auto [v,flip]=witness(p,z,r.Q);if(v<r.Q){if(flip)gate(16,z);gate(32,v,z);log(i,"ccz_linear");done=true;}}
    }
    if(done){saved++;phase++;}else w.put(g);break;
   }
   case 50:{
    V d=q[b]^q[t],p=prod(q[a],d);bool done=true;
    if(p.none()){log(i,"cswap_zero");}
    else if(p==d){gate(34,b,t);log(i,"cswap_swap");}
    else if(p==ONE){gate(17,b);gate(17,t);log(i,"cswap_one");}
    else{auto[x,flip]=witness(p,b,t);if(x<r.Q){if(flip){gate(17,b);gate(17,t);}gate(33,x,b);gate(33,x,t);log(i,"cswap_linear");}else done=false;}
    update(b,p);update(t,p);if(!done)w.put(g);else{saved++;swap_saved++;}break;
   }
   default:cerr<<"unsupported "<<op<<" at "<<i<<endl;return 2;
  }
 }
 assert(frames.empty());w.write(argv[2]);
 cerr<<"rebases "<<rebases<<" saved "<<saved<<" phase "<<phase<<" cleanup "<<cleanup<<" swap "<<swap_saved<<" ops "<<w.ops.size()<<" paid "<<w.a[2].size()<<"\n";
 for(auto const&[k,v]:hist)cerr<<k<<" "<<v<<"\n";
}
