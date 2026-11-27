// Exact parent 4b572141...; coherent two-pad low-weight trial, 901Q.
// Shadow circuits are functions of fixed padding, classical masks and HMR outcomes.
// No syndrome measurement or classical case selection. NOT SUBMISSION.
#include "../zero_phase/common.hpp"
#include <stdexcept>
int xx(int a,int b){return a==2||b==2?2:a^b;}
int aa(int a,int b){return a==0||b==0?0:a==1&&b==1?1:2;}
int assign3(int a,int v,int k){return k==0||a==v?a:k==1?v:2;}
int main(int argc,char**argv){if(argc!=4)return 2;Reader r(argv[1]);if(r.Q!=900)throw runtime_error("width");U B=r.B,tag=r.Q, debt=B+2*r.Q,draw=debt+2;Writer w(r,draw+1);vector<int> Q[2]={vector<int>(r.Q),vector<int>(r.Q)};vector<int>C(r.B),active{1};vector<U> work;vector<bool> isS(r.Q);for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);for(U j=0;j<l;j++){U x;memcpy(&x,p.ptr+8+n+4*j,4);x&=0x7fffffff;if(p.ptr[8]=='S')isS.at(x)=true;else if(p.ptr[8]=='E')C.at(x)=2;else throw runtime_error("register");}}
 for(U j=0;j<r.Q;j++)if(!isS[j])work.push_back(j);if(work.size()!=60)throw runtime_error("ABI");
 auto emit=[&](int op,U a=0,U b=0,U t=0,U bit=0,U cond=0){w.put(Gate{(unsigned char)op,a,b,t,bit,cond});};
 auto push=[&](U c){emit(129,0,0,0,0,c);};auto pop=[&](){emit(1);};auto bx=[&](U c){emit(66,0,0,0,c);};auto cbx=[&](U c,U v){emit(194,0,0,0,c,v);};auto clear=[&](U c){emit(64,0,0,0,c);};
 auto classical_xor=[&](U t,vector<U> const&controls){if(controls.empty()){bx(t);return;}for(size_t i=0;i+1<controls.size();i++)push(controls[i]);cbx(t,controls.back());for(size_t i=0;i+1<controls.size();i++)pop();};
 ifstream f(argv[3]);U v0,n;f>>v0>>n;vector<pair<U,U>>terms(n);for(auto &[a,b]:terms){f>>a>>b;if(a>=r.Q||!isS[a]||b>=24)throw runtime_error("linear term");}vector<U> pads[2];vector<bool> delta(r.Q);for(int j=0;j<2;j++){f>>n;pads[j].resize(n);for(U &q:pads[j]){f>>q;if(q>=r.Q||!isS[q]||Q[j][q])throw runtime_error("pad");Q[j][q]=1;delta[q]=!delta[q];bx(B+j*r.Q+q);}}if(!f)throw runtime_error("config");
 auto selector=[&](){for(auto [a,b]:terms)emit(33,a,work[b]);for(int k=0;k<24;k++)if(!(v0>>k&1))emit(17,work[k]);emit(49,work[0],work[1],work[24]);for(int k=2;k<23;k++)emit(49,work[22+k],work[k],work[23+k]);
 emit(49,work[45],work[23],tag);for(int k=22;k>=2;k--)emit(49,work[22+k],work[k],work[23+k]);emit(49,work[0],work[1],work[24]);for(int k=0;k<24;k++)if(!(v0>>k&1))emit(17,work[k]);for(auto it=terms.rbegin();it!=terms.rend();++it)emit(33,it->first,work[it->second]);};
 auto translate=[&](){for(U q:pads[0])emit(17,q);for(U q=0;q<r.Q;q++)if(delta[q])emit(33,tag,q);};
 selector();translate();
 auto needed=[&](int j,Gate const&g){auto &q=Q[j];U a=g.a,b=g.b,t=g.t;switch(g.op&127){case 0:return true;case 16:return q[a]!=0;case 32:return aa(q[a],q[b])!=0;case 48:return aa(q[a],aa(q[b],q[t]))!=0;case 17:return true;case 18:case 80:return q[a]!=0;case 33:return q[a]!=0;case 49:return aa(q[a],q[b])!=0;case 34:return q[a]==2||q[b]==2||q[a]!=q[b];case 50:return q[a]!=0&&(q[b]==2||q[t]==2||q[b]!=q[t]);case 6:return false;default:throw runtime_error("op "+to_string(g.op));}};
 L mirrored=0,converted=0;
 for(L i=0;i<r.counts[0];i++){
  Gate g=r.read(i);int op=g.op&127;bool cond=g.op&128;int k=active.back();if(cond){if(g.cond>=r.B)throw runtime_error("condition");k=aa(k,C.at(g.cond));}
  if(g.op==129){w.put(g);active.push_back(k);continue;}if(op==1){w.put(g);active.pop_back();continue;}
  if(op==64||op==65||op==66){w.put(g);int v=op==66?xx(C.at(g.bit),1):op-64;C[g.bit]=assign3(C[g.bit],v,k);continue;}
  bool use[2]={k!=0&&needed(0,g),k!=0&&needed(1,g)};
  if(!use[0]&&!use[1]){w.put(g);if(op==80)C[g.bit]=assign3(C[g.bit],2,k);continue;}
  if(cond)push(g.cond);Gate h=g;h.op=op;if(op==18){h.op=80;h.bit=draw;converted++;}w.put(h);
  for(int j=0;j<2;j++)if(use[j]){auto &q=Q[j];U base=B+j*r.Q,a=g.a,b=g.b,t=g.t;auto qctrl=[&](initializer_list<U> a){vector<U> v;for(U x:a)if(q.at(x)==2)v.push_back(base+x);return v;};auto phase=[&](initializer_list<U> a){classical_xor(debt+j,qctrl(a));};switch(op){
   case 0:phase({});break;case 16:phase({a});break;case 32:phase({a,b});break;case 48:phase({a,b,t});break;
   case 17:bx(base+a);q[a]=xx(q[a],k);break;
   case 18:case 80:{auto c=qctrl({a});c.push_back(h.bit);classical_xor(debt+j,c);clear(base+a);q[a]=assign3(q[a],0,k);break;}
   case 33:classical_xor(base+b,qctrl({a}));q[b]=xx(q[b],aa(k,q[a]));break;
   case 49:classical_xor(base+t,qctrl({a,b}));q[t]=xx(q[t],aa(k,aa(q[a],q[b])));break;
   case 34:case 50:{U u=op==34?a:b,v=op==34?b:t;int e=op==34?k:aa(k,q[a]);bool sub=op==50&&q[a]==2;if(sub)push(base+a);cbx(base+u,base+v);cbx(base+v,base+u);cbx(base+u,base+v);if(sub)pop();int x=q[u],y=q[v];q[u]=assign3(x,y,e);q[v]=assign3(y,x,e);break;}
  }mirrored++;}
  if(op==80)C[g.bit]=assign3(C[g.bit],2,k);if(cond)pop();
 }
 if(active.size()!=1)throw runtime_error("unbalanced scope");
 // debt0*(1+tag)+debt1*tag: one selected phase correction.
 emit(128,0,0,0,0,debt);emit(144,tag,0,0,0,debt);emit(144,tag,0,0,0,debt+1);
 translate();selector(); // erase tag from restored original syndrome
 for(U q=0;q<2*r.Q;q++)clear(B+q);clear(debt);clear(debt+1);clear(draw);
 r.Q++;w.write(argv[2]);cerr<<"original_ops "<<r.counts[0]<<" new_ops "<<w.ops.size()<<" original_paid "<<r.counts[1]<<" new_paid "<<w.a[2].size()<<" mirrors "<<mirrored<<" converted_R "<<converted<<"\n";
}
