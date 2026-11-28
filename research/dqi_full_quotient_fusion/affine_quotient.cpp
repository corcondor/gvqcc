// Whole KMB affine quotient, conservative in every classical scope.
// No verifier data, syndrome samples or measurement values in compilation.
#include "native.hpp"
using F=bitset<2048>;
using namespace std;
int base(const Gate&g){return g.op&127;}
struct Hull{
 vector<F> a;unsigned next=1;vector<vector<char>> scopes;
 explicit Hull(U q):a(q){}
 void refresh(){next=1;for(auto &x:a){bool c=x[0];F v=x;v.reset(0);if(v.any()){x.reset();x.set(next++);x[0]=c&&false;}}}
 void unknown(U q){if(next>=2048)refresh();a[q].reset();a[q].set(next++);}
 void touch(U q){for(auto &s:scopes)s[q]=1;}
 void push(){scopes.emplace_back(a.size(),0);}
 void pop(){assert(!scopes.empty());auto t=move(scopes.back());scopes.pop_back();for(U i=0;i<a.size();i++)if(t[i])unknown(i);}
 static bool constant(F x){x.reset(0);return x.none();}
 void set(U q,F f,bool conditional){touch(q);if(!conditional)a[q]=f;else if(a[q]!=f)unknown(q);}
};
struct Stat{L ccx=0,ccz=0,cswap=0,ops=0;void add(Gate g){ops++;ccx+=base(g)==49;ccz+=base(g)==48;cswap+=base(g)==50;}L paid(){return ccx+ccz+cswap;}};
Gate gateLike(Gate g,int b,U x=0,U y=0,U t=0){Gate h{};h.op=b|(g.op&128);h.a=x;h.b=y;h.t=t;h.cond=g.cond;return h;}
F one(){F a;a.set(0);return a;}
int product(F a,F b,F &p){
 if(Hull::constant(a)){p=a[0]?b:F{};return a[0]?2:0;}
 if(Hull::constant(b)){p=b[0]?a:F{};return b[0]?1:0;}
 if(a==b){p=a;return 1;}
 if((a^b)==one()){p.reset();return 0;}
 return -1;
}
vector<Gate> phase(Hull &h,Gate g){
 U q[3]={g.a,g.b,g.t};unsigned allowed=255;
 for(unsigned m=1;m<8;m++){F s;for(int i=0;i<3;i++)if(m>>i&1)s^=h.a[q[i]];
  if(!Hull::constant(s))continue;
  for(unsigned x=0;x<8;x++)if((__builtin_parity(x&m))!=s[0])allowed&=~(1u<<x);
 }
 assert(allowed);if(allowed==255)return{g};
 unsigned mon[7]={0,1,2,4,3,5,6},truth[7]={};for(int j=0;j<7;j++)for(unsigned x=0;x<8;x++)if((x&mon[j])==mon[j])truth[j]|=1u<<x;
 unsigned want=128&allowed;int best=-1;
 for(int k=0;k<128;k++){if(best>=0&&__builtin_popcount(k)>=__builtin_popcount(best))continue;unsigned t=0;for(int j=0;j<7;j++)if(k>>j&1)t^=truth[j];if((t&allowed)==want)best=k;}
 if(best<0)return{g};vector<Gate> r;
 for(int j=0;j<7;j++)if(best>>j&1){if(j==0)r.push_back(gateLike(g,0));else if(j<4)r.push_back(gateLike(g,16,q[j-1]));else{auto t=mon[j];int a=__builtin_ctz(t),b=__builtin_ctz(t^(1u<<a));r.push_back(gateLike(g,32,q[a],q[b]));}}
 return r;
}
int main(int argc,char**argv){
 assert(argc==3);Reader r(argv[1]);Hull h(r.Q);Writer w(r,r.B);Stat old,neu;L xsave=0,zsave=0,refreshes=0;
 for(auto p:r.regs){U nl,rl;memcpy(&nl,p.ptr,4);memcpy(&rl,p.ptr+4,4);assert(p.len>=8+nl+4ull*rl);for(U j=0;j<rl;j++){U id;memcpy(&id,p.ptr+8+nl+4*j,4);if(id&0x80000000){id&=0x7fffffff;assert(id<r.Q);h.unknown(id);}}}
 auto emit=[&](Gate g){w.put(g);neu.add(g);};
 for(L i=0;i<r.counts[0];i++){Gate g=r.read(i);old.add(g);int k=base(g);bool cond=g.op&128;U a=g.a,b=g.b,t=g.t;
  if(g.op==0x81){h.push();emit(g);continue;}
  if(g.op==1){h.pop();emit(g);continue;}
  if(k==49){F p;int v=product(h.a[a],h.a[b],p);
   if(v>=0){xsave++;if(p.any()){if(p==one())emit(gateLike(g,17,t));else if(p==h.a[a])emit(gateLike(g,33,a,t));else if(p==h.a[b])emit(gateLike(g,33,b,t));else assert(false);}
     F f=h.a[t]^p;h.set(t,f,cond);
   }else{emit(g);h.touch(t);h.unknown(t);}
  }else if(k==48){auto z=phase(h,g);if(z.size()!=1||!(z[0]==g))zsave++;for(auto g2:z)emit(g2);}
  else {emit(g);
   if(k==17)h.set(a,h.a[a]^one(),cond);
   else if(k==33)h.set(b,h.a[b]^h.a[a],cond);
   else if(k==34){F x=h.a[a],y=h.a[b];h.set(a,y,cond);h.set(b,x,cond);}
   else if(k==50){F x=h.a[b],y=h.a[t];if(Hull::constant(h.a[a])){if(h.a[a][0]){h.set(b,y,cond);h.set(t,x,cond);}}else if(x!=y){h.touch(b);h.touch(t);h.unknown(b);h.unknown(t);}}
   else if(k==18||k==80)h.set(a,F{},cond);
   else if(k==0||k==16||k==19||k==32||k==64||k==65||k==66||k==6||k==7||k==71||k==23){}
   else {int n=(g.op&48)>>4;for(U q:vector<U>{a,b,t}){if(!n--)break;assert(q<r.Q);h.touch(q);h.unknown(q);}}
  }
 }
 assert(h.scopes.empty());assert(old.paid()>=neu.paid());assert(old.paid()-neu.paid()==xsave+zsave);
 w.write(argv[2]);cout<<"{\"old_ops\":"<<old.ops<<",\"new_ops\":"<<neu.ops<<",\"old_paid\":"<<old.paid()<<",\"new_paid\":"<<neu.paid()<<",\"ccx_reductions\":"<<xsave<<",\"ccz_reductions\":"<<zsave<<",\"q\":"<<r.Q<<"}\n";
}
