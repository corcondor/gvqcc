// Exact dependent two/three-product synthesis on complete KMBs.
// The active covector and target spans have dimension <=6 and <=3;
// no sampled acceptance, no extra quantum wires, no changes to HMR order.
#include <bits/stdc++.h>
#include "../dqi_whole_root_frame/native.hpp"
using W=uint64_t;
static W one(int x){return W(1)<<x;}
static int bit(W x,int i){return (x>>i)&1;}
static int parity(W x){return __builtin_parityll(x);}
static int pop(W x){return __builtin_popcountll(x);}
struct Basis{
 W val[64]={},coef[64]={};vector<W> vs;
 int add(W x){for(int j=63;j>=0;j--)if(bit(x,j)){if(val[j])x^=val[j];else{int k=vs.size();val[j]=x;coef[j]=one(k);vs.push_back(x);return k;}}return -1;}
 W coord(W x)const{W c=0;for(int j=63;j>=0;j--)if(bit(x,j)){assert(val[j]);x^=val[j];c^=coef[j];}assert(!x);return c;}
};
struct O{int op,a,b,t;};
static bool equal(O a,O b){return tie(a.op,a.a,a.b,a.t)==tie(b.op,b.a,b.b,b.t);}
static void put(vector<O>&v,O g){if(!v.empty()&&equal(v.back(),g))v.pop_back();else v.push_back(g);}
static int paid(const vector<O>&v){return count_if(v.begin(),v.end(),[](O x){return x.op==49;});}
static W run(W s,const vector<O>&v){for(auto g:v){
 if(g.op==17)s^=one(g.a);
 else if(g.op==33)s^=W(bit(s,g.a))<<g.b;
 else if(g.op==34){if(bit(s,g.a)^bit(s,g.b))s^=one(g.a)|one(g.b);}
 else if(g.op==49)s^=W(bit(s,g.a)&bit(s,g.b))<<g.t;
 else abort();}return s;}
struct Shear{W a,b,u;int ca,cb;};
struct Frame{
 vector<W> row,ic;W c=0;vector<Shear> ss;vector<O> affine;
 Frame(int n,const vector<O>&v):row(n),ic(n){
  for(int i=0;i<n;i++)row[i]=ic[i]=one(i);
  for(auto g:v){
   int a=g.a,b=g.b;
   if(g.op==49){ss.push_back({row[a],row[b],ic[g.t],bit(c,a),bit(c,b)});continue;}
   affine.push_back(g);
   if(g.op==17)c^=one(a);
   else if(g.op==33){row[b]^=row[a];ic[a]^=ic[b];if(bit(c,a))c^=one(b);}
   else if(g.op==34){swap(row[a],row[b]);swap(ic[a],ic[b]);if(bit(c,a)^bit(c,b))c^=one(a)|one(b);}
   else abort();
  }
  for(auto s:ss)assert(!parity(s.a&s.u)&&!parity(s.b&s.u));
 }
};
struct Truth{
 int r,n;W all;array<W,6> var{};
 Truth(int rr):r(rr),n(1<<rr),all(n==64?~W(0):one(n)-1){
  for(int i=0;i<r;i++)for(int x=0;x<n;x++)if(bit(x,i))var[i]|=one(x);
 }
 W form(int m,int c=0)const{W x=c?all:0;for(int i=0;i<r;i++)if(bit(m,i))x^=var[i];return x;}
 W linear(W x)const{W a=bit(x,0)?all:0;for(int i=0;i<r;i++)if(bit(x,one(i))^bit(x,0))a^=var[i];return a;}
 W nonlin(W x)const{return x^linear(x);}
 W shift(W f,int beta)const{for(int i=0;i<r;i++)if(bit(beta,i)){int d=1<<i;f=((f&~var[i])<<d)|((f&var[i])>>d);}return f&all;}
};
struct Product{W p;int a,b,ca,cb;};
struct Products{vector<Product> list;unordered_map<W,vector<int>> by;};
static map<pair<int,int>,Products> productCache;
static const Products& products(const Truth&T,int beta){
 auto k=make_pair(T.r,beta);auto hit=productCache.find(k);if(hit!=productCache.end())return hit->second;
 Products z;set<W> seen;
 for(int a=1;a<(1<<T.r);a++)if(!parity(a&beta))
  for(int b=a+1;b<(1<<T.r);b++)if(!parity(b&beta))
   for(int ca=0;ca<2;ca++)for(int cb=0;cb<2;cb++){
    W p=T.form(a,ca)&T.form(b,cb);W f=T.nonlin(p);if(!f||!seen.insert(p).second)continue;
    z.by[f].push_back(z.list.size());z.list.push_back({p,a,b,ca,cb});
   }
 return productCache.emplace(k,move(z)).first->second;
}
using H=array<W,3>;
static int rankN(const Truth&T,const H&h,int s){
 W v[64]={};int rank=0;for(int j=0;j<s;j++){W f=T.nonlin(h[j]);for(int i=63;i>=0;i--)if(bit(f,i)){if(v[i])f^=v[i];else{v[i]=f;rank++;break;}}}return rank;
}
struct Choice{int d;Product p;};
struct Plan{bool ok=false;vector<Choice> steps;H residual{};};
struct Space{
 Basis b,w;vector<int> beta;H h{};Truth T;
 Space(const Frame&f):T(0){
  for(auto g:f.ss){b.add(g.a);b.add(g.b);w.add(g.u);}
  assert(b.vs.size()<=6&&w.vs.size()<=3);T=Truth(b.vs.size());
  beta.resize(1<<w.vs.size());
  for(int d=1;d<(int)beta.size();d++){W u=direction(d);int v=0;for(int i=0;i<T.r;i++)v|=parity(b.vs[i]&u)<<i;beta[d]=v;}
  for(auto g:f.ss){W a=T.form(b.coord(g.a),g.ca),bb=T.form(b.coord(g.b),g.cb);
   for(int j=0;j<(int)w.vs.size();j++){if(parity(g.a&w.vs[j]))a^=h[j];if(parity(g.b&w.vs[j]))bb^=h[j];}
   W p=a&bb;int d=w.coord(g.u);for(int j=0;j<(int)w.vs.size();j++)if(bit(d,j))h[j]^=p;
  }
 }
 int s()const{return w.vs.size();}
 W direction(int d)const{W u=0;for(int j=0;j<(int)w.vs.size();j++)if(bit(d,j))u^=w.vs[j];return u;}
 W covector(int d)const{W a=0;for(int i=0;i<T.r;i++)if(bit(d,i))a^=b.vs[i];return a;}
 H compose(H h,int d,W p)const{
  H z{};for(int j=0;j<s();j++)z[j]=h[j]^(p&((bit(d,j)?T.all:0)^h[j]^T.shift(h[j],beta[d])));return z;
 }
 string key(int limit)const{
  string k; k.push_back(char(T.r));k.push_back(char(s()));k.push_back(char(limit));
  for(int x:beta)k.push_back(char(x));for(W x:h)k.append((char*)&x,8);return k;
 }
};
static unordered_map<string,Plan> planCache;
static L product_trials=0,cache_hits=0,rank_blocked=0;
static Plan findOne(const Space&S,H h){
 int r=rankN(S.T,h,S.s());if(r==0)return {true,{},h};if(r!=1)return {};
 W f=0;for(int j=0;j<S.s();j++)if((f=S.T.nonlin(h[j])))break;
 for(int d=1;d<(int)S.beta.size();d++){
  auto&ps=products(S.T,S.beta[d]);auto it=ps.by.find(f);if(it==ps.by.end())continue;
  for(int i:it->second){auto p=ps.list[i];product_trials++;auto z=S.compose(h,d,p.p);
   if(rankN(S.T,z,S.s())==0)return {true,{{d,p}},z};
  }
 }return {};
}
static Plan solve(const Space&S,int limit){
 int rank=rankN(S.T,S.h,S.s());if(rank>limit){rank_blocked++;return {};}
 string key=S.key(limit);auto it=planCache.find(key);if(it!=planCache.end()){cache_hits++;return it->second;}
 Plan q=findOne(S,S.h);if(q.ok||limit==1){planCache.emplace(move(key),q);return q;}
 for(int d=1;d<(int)S.beta.size();d++){auto&ps=products(S.T,S.beta[d]);for(auto p:ps.list){
  product_trials++;auto h=S.compose(S.h,d,p.p);if(rankN(S.T,h,S.s())>1)continue;
  auto z=findOne(S,h);if(z.ok){z.steps.insert(z.steps.begin(),{d,p});planCache.emplace(move(key),z);return z;}
 }}
 planCache.emplace(move(key),q);return q;
}
// Gaussian affine synthesis with exact inverse row operations.
static vector<O> linear(vector<W> r,W c){
 int n=r.size();vector<O> v;
 for(int j=0;j<n;j++){int k=j;while(k<n&&!bit(r[k],j))k++;assert(k<n);
  if(k!=j){swap(r[k],r[j]);v.push_back({34,j,k,0});}
  for(int i=0;i<n;i++)if(i!=j&&bit(r[i],j)){r[i]^=r[j];v.push_back({33,j,i,0});}
 }
 reverse(v.begin(),v.end());for(int i=0;i<n;i++)if(bit(c,i))v.push_back({17,i,0,0});return v;
}
static vector<O> synth(W l,W m,W u,int ca,int cb,int n){
 assert(u&&!parity(l&u)&&!parity(m&u));vector<O> best;
 for(int t=0;t<n;t++)if(bit(u,t)){
  W arow=l&~one(t),brow=m&~one(t);
  for(int a=0;a<n;a++)if(a!=t)for(int b=0;b<n;b++)if(b!=a&&b!=t&&(bit(arow,a)*bit(brow,b)^bit(arow,b)*bit(brow,a))){
   vector<O> pre;for(int i=0;i<n;i++)if(i!=t&&bit(u,i))pre.push_back({33,t,i,0});
   vector<W> two={W(bit(arow,a))|(W(bit(arow,b))<<1),W(bit(brow,a))|(W(bit(brow,b))<<1)};
   for(auto g:linear(two,0))pre.push_back({g.op,g.a?b:a,g.b?b:a,0});
   for(int j=0;j<n;j++)if(j!=t&&j!=a&&j!=b){if(bit(arow,j))pre.push_back({33,j,a,0});if(bit(brow,j))pre.push_back({33,j,b,0});}
   if(ca)pre.push_back({17,a,0,0});if(cb)pre.push_back({17,b,0,0});
   if(best.empty()||2*pre.size()+1<best.size()){best=pre;best.push_back({49,a,b,t});best.insert(best.end(),pre.rbegin(),pre.rend());}
  }
 }assert(!best.empty());return best;
}
static vector<O> emit(const Frame&f,const Space&S,const Plan&p){
 int n=f.row.size();vector<O> v;
 for(auto step:p.steps)for(auto g:synth(S.covector(step.p.a),S.covector(step.p.b),S.direction(step.d),step.p.ca,step.p.cb,n))put(v,g);
 vector<W> rows(n);W c=0;for(int i=0;i<n;i++)rows[i]=one(i);
 for(int j=0;j<S.s();j++){W h=p.residual[j];assert(S.T.nonlin(h)==0);W u=S.w.vs[j],form=0;
  for(int i=0;i<S.T.r;i++)if(bit(h,one(i))^bit(h,0))form^=S.b.vs[i];
  for(int i=0;i<n;i++)if(bit(u,i))rows[i]^=form;if(bit(h,0))c^=u;
 }
 vector<O>a=linear(rows,c);a.insert(a.end(),f.affine.begin(),f.affine.end());
 vector<W> fin(n);W fc=f.c;
 for(int i=0;i<n;i++){for(int j=0;j<n;j++)if(bit(f.row[i],j))fin[i]^=rows[j];if(parity(f.row[i]&c))fc^=one(i);}
 auto b=linear(fin,fc);for(auto g:(a.size()<=b.size()?a:b))put(v,g);
 return v;
}
// Independent affine-coset certificate. For a fixed union control
// coordinate all nonlinear increments are fixed; only the affine part
// changes along a kernel direction. This checks ALL input states.
static pair<L,L> verify(const vector<O>&a,const vector<O>&b,int n){
 Frame A(n,a),B(n,b);Basis cov;for(auto f:{&A,&B})for(auto g:f->ss){cov.add(g.a);cov.add(g.b);}
 int r=cov.vs.size();assert(r<=10);int size=1<<r;
 vector<W> rep(size);vector<char> ok(size);vector<W> ker;ok[0]=1;
 for(int j=0;j<n;j++){int c=0;for(int i=0;i<r;i++)c|=bit(cov.vs[i],j)<<i;
  if(ok[c])ker.push_back(one(j)^rep[c]);else{
   auto old=ok;for(int x=0;x<size;x++)if(old[x]){assert(!ok[x^c]);ok[x^c]=1;rep[x^c]=rep[x]^one(j);}
  }
 }
 assert((int)ker.size()==n-r&&all_of(ok.begin(),ok.end(),[](char x){return x;}));
 for(W x:rep)if(run(x,a)!=run(x,b))abort();
 W a0=run(0,a),b0=run(0,b);for(W k:ker)if((run(k,a)^a0)!=(run(k,b)^b0))abort();
 return {size,ker.size()};
}
static L windows=0,wide=0,accepted=0,checks=0,kchecks=0,saved=0;static long long savedOps=0;
static bool rewrite(vector<Gate> const&in,vector<Gate>&out,L pos,ostream&log){
 windows++;vector<U> wires;unordered_map<U,int> index;
 auto id=[&](U q){auto it=index.find(q);if(it!=index.end())return it->second;int z=wires.size();wires.push_back(q);index[q]=z;return z;};
 vector<O>a;for(auto g:in){int i=id(g.a),j=g.op==17?0:id(g.b),t=g.op==49?id(g.t):0;a.push_back({g.op,i,j,t});}
 int n=wires.size(),p=paid(a);assert(p==2||p==3);
 if(n>64){wide++;return false;}
 Frame f(n,a);Space S(f);auto plan=solve(S,p-1);if(!plan.ok)return false;
 auto b=emit(f,S,plan);int np=paid(b);assert(np<p);
 // Keep instruction inflation bounded, but never discard a paid saving
 // merely because no exact short motif was available.
 if(b.size()>a.size()+512)return false;
 auto [c,k]=verify(a,b,n);checks+=c;kchecks+=k;accepted++;saved+=p-np;savedOps+=(long long)a.size()-b.size();
 for(auto g:b)out.push_back({(unsigned char)g.op,wires[g.a],g.op==17?0:wires[g.b],g.op==49?wires[g.t]:0});
 log<<pos<<"\t"<<in.size()<<"\t"<<out.size()<<"\t"<<p<<"\t"<<np<<"\t"<<n<<"\t"<<c<<"\t"<<k<<"\n";return true;
}
static void selftest(){
 // Dependent third product: after first target t ^= a*b, the
 // next two equal controlled products cancel across an affine echo.
 vector<Gate> g={{49,0,1,2},{33,2,3},{49,2,4,5},{33,2,3},{49,2,4,5}};
 vector<Gate> o;ostringstream log;assert(rewrite(g,o,0,log));
 assert(count_if(o.begin(),o.end(),[](Gate h){return h.op==49;})==1);
 // Two different products with the same target and common factor.
 g={{49,0,1,3},{49,0,2,3}};o.clear();assert(rewrite(g,o,0,log));
 assert(count_if(o.begin(),o.end(),[](Gate h){return h.op==49;})==1);
 cerr<<"selftest exact dependent/covector contraction passed\n";
}
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--selftest"){selftest();return 0;}
 if(argc!=4)return 2;
 selftest();windows=wide=accepted=checks=kchecks=saved=rank_blocked=cache_hits=product_trials=0;savedOps=0;
 Reader r(argv[1]);Writer w(r,r.B);deque<Gate> buf;L pos=0;ofstream sites(argv[3]);int c=0;
 auto push=[&](Gate g){w.put(g);};
 auto cut=[&](size_t take){for(size_t i=0;i<take;i++)buf.pop_front();pos+=take;};
 auto flush_prefix=[&](size_t take){for(size_t i=0;i<take;i++)push(buf[i]);cut(take);};
 auto strip=[&](){while(!buf.empty()&&buf.front().op!=49)flush_prefix(1);};
 auto try_prefix=[&](int want){int pc=0;size_t n=0;for(;n<buf.size();n++)if(buf[n].op==49&&++pc==want){n++;break;}if(pc!=want)return false;
  vector<Gate> in(buf.begin(),buf.begin()+n),out;if(!rewrite(in,out,pos,sites))return false;
  for(auto g:out)push(g);cut(n);c-=want;strip();return true;};
 auto advance=[&](){assert(c);flush_prefix(1);c--;strip();};
 auto finish=[&](){while(c>=2){if(c>=3&&try_prefix(3))continue;if(try_prefix(2))continue;advance();}
  if(c)advance();while(!buf.empty())flush_prefix(1);assert(c==0);};
 for(L i=0;i<r.counts[0];i++){auto g=r.read(i);
  if(g.op!=17&&g.op!=33&&g.op!=34&&g.op!=49){finish();push(g);pos++;continue;}
  if(buf.empty()&&g.op!=49){push(g);pos++;continue;}
  buf.push_back(g);if(g.op==49)c++;
  if(c==3){if(!try_prefix(3)&&!try_prefix(2))advance();}
  if(buf.size()>=512)finish();
 }finish();assert(pos==r.counts[0]);w.write(argv[2]);
 cout<<"{\"q\":"<<r.Q<<",\"old_ops\":"<<r.counts[0]<<",\"new_ops\":"<<w.ops.size()<<",\"windows\":"<<windows<<",\"wide\":"<<wide<<",\"rank_blocked\":"<<rank_blocked<<",\"accepted\":"<<accepted<<",\"saved_static_paid\":"<<saved<<",\"saved_ops\":"<<savedOps<<",\"coset_checks\":"<<checks<<",\"kernel_checks\":"<<kchecks<<",\"product_trials\":"<<product_trials<<",\"cache_hits\":"<<cache_hits<<"}\n";
}
