// Exact #247 tape with two tag-free padding choices and two classical
// fixed-pad shadows. The donor itself is not replaced.
#include "native.hpp"
#include <stdexcept>
int xx(int a,int b){return a==2||b==2?2:a^b;}
int aa(int a,int b){return a==0||b==0?0:a==1&&b==1?1:2;}
int assign3(int a,int v,int k){return k==0||a==v?a:k==1?v:2;}
int main(int argc,char**argv){
 assert(argc==6);Reader r(argv[1]),pre(argv[3]),post(argv[4]);assert(r.Q==900&&r.counts[0]==66696654&&r.counts[1]==318333);
 U B=r.B,debt=B+2*r.Q,draw=debt+2,off=draw+1;
 Writer w(r,off+pre.B+post.B);vector<int> Q[2]={vector<int>(r.Q),vector<int>(r.Q)};vector<int>C(r.B),active{1};vector<U>S(840),work;vector<bool>isS(r.Q);
 for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);for(U j=0;j<l;j++){U x;memcpy(&x,p.ptr+8+n+4*j,4);x&=0x7fffffff;if(p.ptr[8]=='S'){U i=stoul(string(p.ptr+9,n-1));assert(i<70&&l==12);S[12*i+j]=x;isS.at(x)=true;}else if(p.ptr[8]=='E')C.at(x)=2;else throw runtime_error("register");}}
 for(U j=0;j<r.Q;j++)if(!isS[j])work.push_back(j);assert(work.size()==60);
 auto emit=[&](int op,U a=0,U b=0,U t=0,U bit=0,U cond=0){w.put(Gate{(unsigned char)op,a,b,t,bit,cond});};
 auto push=[&](U c){emit(129,0,0,0,0,c);};auto pop=[&](){emit(1);};auto bx=[&](U c){emit(66,0,0,0,c);};auto cbx=[&](U c,U v){emit(194,0,0,0,c,v);};auto clear=[&](U c){emit(64,0,0,0,c);};
 auto classical_xor=[&](U t,vector<U> const&controls){if(controls.empty()){bx(t);return;}for(size_t i=0;i+1<controls.size();i++)push(controls[i]);cbx(t,controls.back());for(size_t i=0;i+1<controls.size();i++)pop();};
 vector<U>qm=S;qm.insert(qm.end(),work.begin(),work.end());
 auto fragment=[&](Reader& f,U o){f.reset();assert(f.Q<=r.Q&&f.counts[6]==0);auto cb=[&](U x){U hi=x&0x80000000;x&=0x7fffffff;assert(x<f.B);return (x<2?debt+x:o+x)|hi;};
  for(L i=0;i<f.counts[0];i++){Gate g=f.read(i);int base=g.op&127,n=(g.op&48)>>4;if(base==6)continue;if(n==1)g.a=qm.at(g.a);else if(n==2){g.a=qm.at(g.a);g.b=qm.at(g.b);}else if(n==3){g.a=qm.at(g.a);g.b=qm.at(g.b);g.t=qm.at(g.t);}
   if((g.op&64)&&base!=6&&base!=7)g.bit=cb(g.bit);if(g.op&128)g.cond=cb(g.cond);w.put(g);}
 };
 fragment(pre,off);
 ifstream pin(argv[5]);for(int p=0;p<2;p++)for(int i=0;i<70;i++){U a;pin>>a;assert(pin.good()&&a<4096);for(int j=0;j<12;j++)if((a>>j)&1){U q=S[12*i+j];Q[p][q]=1;emit(65,0,0,0,B+p*r.Q+q);}}
 L mirrored=0,converted=0;
 auto needed=[&](int p,Gate const&g){auto&q=Q[p];U a=g.a,b=g.b,t=g.t;switch(g.op&127){case 0:return true;case 16:return q[a]!=0;case 32:return aa(q[a],q[b])!=0;case 48:return aa(q[a],aa(q[b],q[t]))!=0;case 17:return true;case 18:case 80:return q[a]!=0;case 33:return q[a]!=0;case 49:return aa(q[a],q[b])!=0;case 34:return q[a]==2||q[b]==2||q[a]!=q[b];case 50:return q[a]!=0&&(q[b]==2||q[t]==2||q[b]!=q[t]);case 6:return false;default:throw runtime_error("op "+to_string(g.op));}};
 for(L i=0;i<r.counts[0];i++){
  Gate g=r.read(i);int op=g.op&127;bool cond=g.op&128;int k=active.back();if(cond){assert(g.cond<r.B);k=aa(k,C.at(g.cond));}
  if(g.op==129){w.put(g);active.push_back(k);continue;}if(op==1){w.put(g);assert(active.size()>1);active.pop_back();continue;}
  if(op==64||op==65||op==66){w.put(g);int v=op==66?xx(C.at(g.bit),1):op-64;C[g.bit]=assign3(C[g.bit],v,k);continue;}
  bool use[2]={k!=0&&needed(0,g),k!=0&&needed(1,g)};
  if(!use[0]&&!use[1]){w.put(g);if(op==80)C[g.bit]=assign3(C[g.bit],2,k);continue;}
  if(cond)push(g.cond);Gate h=g;h.op=op;if(op==18){h.op=80;h.bit=draw;converted++;}w.put(h);
  for(int p=0;p<2;p++)if(use[p]){
   auto&q=Q[p];U b0=B+p*r.Q,a=g.a,b=g.b,t=g.t;
   auto qctrl=[&](initializer_list<U> v){vector<U>u;for(U j:v)if(q.at(j)==2)u.push_back(b0+j);return u;};
   auto phase=[&](initializer_list<U> v){classical_xor(debt+p,qctrl(v));};
   switch(op){
    case 0:phase({});break;case 16:phase({a});break;case 32:phase({a,b});break;case 48:phase({a,b,t});break;
    case 17:bx(b0+a);q[a]=xx(q[a],k);break;
    case 18:case 80:{auto c=qctrl({a});c.push_back(h.bit);classical_xor(debt+p,c);clear(b0+a);q[a]=assign3(q[a],0,k);break;}
    case 33:classical_xor(b0+b,qctrl({a}));q[b]=xx(q[b],aa(k,q[a]));break;
    case 49:classical_xor(b0+t,qctrl({a,b}));q[t]=xx(q[t],aa(k,aa(q[a],q[b])));break;
    case 34:case 50:{U u=op==34?a:b,v=op==34?b:t;int ff=op==34?k:aa(k,q[a]);bool sub=op==50&&q[a]==2;if(sub)push(b0+a);cbx(b0+u,b0+v);cbx(b0+v,b0+u);cbx(b0+u,b0+v);if(sub)pop();int x=q[u],y=q[v];q[u]=assign3(x,y,ff);q[v]=assign3(y,x,ff);break;}
   }mirrored++;
  }
  if(op==80)C[g.bit]=assign3(C[g.bit],2,k);if(cond)pop();
 }
 assert(active.size()==1);
 fragment(post,off+pre.B);for(U q=B;q<w.bits;q++)clear(q);
 w.write(argv[2]);cerr<<"original_ops "<<r.counts[0]<<" new_ops "<<w.ops.size()<<" original_paid "<<r.counts[1]<<" new_paid "<<w.a[2].size()<<" mirrors "<<mirrored<<" converted_R "<<converted<<"\n";
}
