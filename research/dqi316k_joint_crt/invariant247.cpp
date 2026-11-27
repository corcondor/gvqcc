// Tag-free invariant extension-pad repair on exact #247, using shared
// original donor arithmetic and classical HMR repayment (no syndrome read).
#include "native.hpp"
#include <stdexcept>
int xx(int a,int b){return a==2||b==2?2:a^b;}
int aa(int a,int b){return a==0||b==0?0:a==1&&b==1?1:2;}
int assign3(int a,int v,int k){return k==0||a==v?a:k==1?v:2;}
int main(int argc,char**argv){
 assert(argc==5);Reader r(argv[1]),f(argv[3]);assert(r.Q==900&&r.counts[0]==66696654&&r.counts[1]==318333);
 U B=r.B,debt=B+r.Q,draw=debt+1,off=draw+1;
 Writer w(r,off+2*f.B);vector<int> Q(r.Q),C(r.B),active{1};vector<U>S(840),work;vector<bool>isS(r.Q);
 for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);for(U j=0;j<l;j++){U x;memcpy(&x,p.ptr+8+n+4*j,4);x&=0x7fffffff;if(p.ptr[8]=='S'){U i=stoul(string(p.ptr+9,n-1));assert(i<70&&l==12);S[12*i+j]=x;isS.at(x)=true;}else if(p.ptr[8]=='E')C.at(x)=2;else throw runtime_error("register");}}
 for(U j=0;j<r.Q;j++)if(!isS[j])work.push_back(j);assert(work.size()==60);
 auto emit=[&](int op,U a=0,U b=0,U t=0,U bit=0,U cond=0){w.put(Gate{(unsigned char)op,a,b,t,bit,cond});};
 auto push=[&](U c){emit(129,0,0,0,0,c);};auto pop=[&](){emit(1);};auto bx=[&](U c){emit(66,0,0,0,c);};auto cbx=[&](U c,U v){emit(194,0,0,0,c,v);};auto clear=[&](U c){emit(64,0,0,0,c);};
 auto classical_xor=[&](U t,vector<U> const&controls){if(controls.empty()){bx(t);return;}for(size_t i=0;i+1<controls.size();i++)push(controls[i]);cbx(t,controls.back());for(size_t i=0;i+1<controls.size();i++)pop();};
 auto qctrl=[&](initializer_list<U> a){vector<U> v;for(U j:a)if(Q.at(j)==2)v.push_back(B+j);return v;};
 vector<U>qm=S;qm.insert(qm.end(),work.begin(),work.end());
 auto fragment=[&](U o){f.reset();assert(f.Q<=r.Q&&f.counts[6]==0);auto cb=[&](U x){U hi=x&0x80000000;x&=0x7fffffff;assert(x<f.B);return (x==0?debt:o+x)|hi;};
  for(L i=0;i<f.counts[0];i++){Gate g=f.read(i);int base=g.op&127,n=(g.op&48)>>4;if(base==6)continue;if(n==1)g.a=qm.at(g.a);else if(n==2){g.a=qm.at(g.a);g.b=qm.at(g.b);}else if(n==3){g.a=qm.at(g.a);g.b=qm.at(g.b);g.t=qm.at(g.t);}
   if((g.op&64)&&base!=6&&base!=7)g.bit=cb(g.bit);if(g.op&128)g.cond=cb(g.cond);w.put(g);}
 };
 fragment(off);
 ifstream pin(argv[4]);for(int i=0;i<70;i++){U a;pin>>a;assert(pin.good()&&a<4096);for(int j=0;j<12;j++)if((a>>j)&1){U q=S[12*i+j];Q[q]=1;emit(65,0,0,0,B+q);}}
 L mirrored=0,converted=0;
 for(L i=0;i<r.counts[0];i++){
  Gate g=r.read(i);int op=g.op&127;bool cond=g.op&128;int k=active.back();if(cond){assert(g.cond<r.B);k=aa(k,C.at(g.cond));}
  if(g.op==129){w.put(g);active.push_back(k);continue;}if(op==1){w.put(g);assert(active.size()>1);active.pop_back();continue;}
  if(op==64||op==65||op==66){w.put(g);int v=op==66?xx(C.at(g.bit),1):op-64;C[g.bit]=assign3(C[g.bit],v,k);continue;}
  U a=g.a,b=g.b,t=g.t;bool needed=false;
  switch(op){case 0:needed=true;break;case 16:needed=Q[a]!=0;break;case 32:needed=aa(Q[a],Q[b])!=0;break;case 48:needed=aa(Q[a],aa(Q[b],Q[t]))!=0;break;case 17:needed=true;break;case 18:case 80:needed=Q[a]!=0;break;case 33:needed=Q[a]!=0;break;case 49:needed=aa(Q[a],Q[b])!=0;break;case 34:needed=Q[a]==2||Q[b]==2||Q[a]!=Q[b];break;case 50:needed=Q[a]!=0&&(Q[b]==2||Q[t]==2||Q[b]!=Q[t]);break;case 6:break;default:throw runtime_error("op "+to_string(op));}
  if(k==0||!needed){w.put(g);if(op==80)C[g.bit]=assign3(C[g.bit],2,k);continue;}
  if(cond)push(g.cond);Gate h=g;h.op=op;if(op==18){h.op=80;h.bit=draw;converted++;}w.put(h);
  auto phase=[&](initializer_list<U> ctrl){classical_xor(debt,qctrl(ctrl));};
  switch(op){
   case 0:phase({});break;case 16:phase({a});break;case 32:phase({a,b});break;case 48:phase({a,b,t});break;
   case 17:bx(B+a);Q[a]=xx(Q[a],k);break;
   case 18:case 80:{auto c=qctrl({a});c.push_back(h.bit);classical_xor(debt,c);clear(B+a);Q[a]=assign3(Q[a],0,k);if(op==80)C[g.bit]=assign3(C[g.bit],2,k);break;}
   case 33:classical_xor(B+b,qctrl({a}));Q[b]=xx(Q[b],aa(k,Q[a]));break;
   case 49:classical_xor(B+t,qctrl({a,b}));Q[t]=xx(Q[t],aa(k,aa(Q[a],Q[b])));break;
   case 34:case 50:{U u=op==34?a:b,v=op==34?b:t;int ff=op==34?k:aa(k,Q[a]);bool sub=op==50&&Q[a]==2;if(sub)push(B+a);cbx(B+u,B+v);cbx(B+v,B+u);cbx(B+u,B+v);if(sub)pop();int x=Q[u],y=Q[v];Q[u]=assign3(x,y,ff);Q[v]=assign3(y,x,ff);break;}
  }
  if(cond)pop();mirrored++;
 }
 assert(active.size()==1);
 fragment(off+f.B);for(U q=B;q<w.bits;q++)clear(q);
 w.write(argv[2]);cerr<<"original_ops "<<r.counts[0]<<" new_ops "<<w.ops.size()<<" original_paid "<<r.counts[1]<<" new_paid "<<w.a[2].size()<<" mirrors "<<mirrored<<" converted_R "<<converted<<"\n";
}
