// Partial zero-input phase repair: not a full decoder repair.
#include "common.hpp"
#include <stdexcept>
int xx(int a,int b){return a==2||b==2?2:a^b;}
int aa(int a,int b){return a==0||b==0?0:a==1&&b==1?1:2;}
int assign3(int a,int v,int k){return k==0||a==v?a:k==1?v:2;}
int main(int argc,char**argv){if(argc!=3)return 2;Reader r(argv[1]);U B=r.B, debt=B+r.Q, draw=debt+1,undo=draw+1,flagdraw=undo+1;Writer w(r,flagdraw+1);vector<int> Q(r.Q),C(r.B),active{1};vector<U> S,guardS,work;vector<bool> isS(r.Q);for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);for(U j=0;j<l;j++){U x;memcpy(&x,p.ptr+8+n+4*j,4);x&=0x7fffffff;if(p.ptr[8]=='S'){S.push_back(x);isS.at(x)=true;if(stoul(string(p.ptr+9,n-1))<35)guardS.push_back(x);}else if(p.ptr[8]=='E')C.at(x)=2;else throw runtime_error("register");}}
 for(U j=0;j<r.Q;j++)if(!isS[j])work.push_back(j);if(S.size()!=840||guardS.size()!=420||work.size()!=60||r.Q!=900)throw runtime_error("ABI");
 auto emit=[&](int op,U a=0,U b=0,U t=0,U bit=0,U cond=0){w.put(Gate{(unsigned char)op,a,b,t,bit,cond});};
 auto push=[&](U c){emit(129,0,0,0,0,c);}; auto pop=[&](){emit(1);}; auto bx=[&](U c){emit(66,0,0,0,c);};auto cbx=[&](U c,U v){emit(194,0,0,0,c,v);};auto clear=[&](U c){emit(64,0,0,0,c);};
 auto classical_xor=[&](U t,vector<U> const&controls){if(controls.empty()){bx(t);return;}for(size_t i=0;i+1<controls.size();i++)push(controls[i]);cbx(t,controls.back());for(size_t i=0;i+1<controls.size();i++)pop();};
 auto qctrl=[&](initializer_list<U> a){vector<U> v;for(U j:a)if(Q.at(j)==2)v.push_back(B+j);return v;};
 L orig_phase=0,mirrored=0,converted=0,shadow_ops=0;
 for(L i=0;i<r.counts[0];i++){
  Gate g=r.read(i);int op=g.op&127;bool cond=g.op&128;int k=active.back();if(cond){if(g.cond>=r.B)throw runtime_error("bad original condition");k=aa(k,C.at(g.cond));}
  if(g.op==129){w.put(g);active.push_back(k);continue;}if(op==1){w.put(g);active.pop_back();continue;}
  if(op==64||op==65||op==66){w.put(g);int v=op==66?xx(C.at(g.bit),1):op-64;C[g.bit]=assign3(C[g.bit],v,k);continue;}
  U a=g.a,b=g.b,t=g.t;bool needed=false;
  switch(op){case 0:needed=true;break;case 16:needed=Q[a]!=0;break;case 32:needed=aa(Q[a],Q[b])!=0;break;case 48:needed=aa(Q[a],aa(Q[b],Q[t]))!=0;break;case 17:needed=true;break;case 18:case 80:needed=Q[a]!=0;break;case 33:needed=Q[a]!=0;break;case 49:needed=aa(Q[a],Q[b])!=0;break;case 34:needed=Q[a]==2||Q[b]==2||Q[a]!=Q[b];break;case 50:needed=Q[a]!=0&&(Q[b]==2||Q[t]==2||Q[b]!=Q[t]);break;case 6:break;default:throw runtime_error("op "+to_string(op));}
  if(op==0||op==16||op==32||op==48||op==18||op==80)orig_phase++;
  if(k==0||!needed){w.put(g);if(op==80)C[g.bit]=assign3(C[g.bit],2,k);continue;}
  L n=w.ops.size();if(cond)push(g.cond);Gate h=g;h.op=op;
  if(op==18){h.op=80;h.bit=draw;converted++;}w.put(h);
  auto phase=[&](initializer_list<U> ctrl){classical_xor(debt,qctrl(ctrl));};
  switch(op){
   case 0:phase({});break;case 16:phase({a});break;case 32:phase({a,b});break;case 48:phase({a,b,t});break;
   case 17:bx(B+a);Q[a]=xx(Q[a],k);break;
   case 18:case 80:{vector<U> c=qctrl({a});c.push_back(h.bit);classical_xor(debt,c);clear(B+a);Q[a]=assign3(Q[a],0,k);if(op==80)C[g.bit]=assign3(C[g.bit],2,k);break;}
   case 33:classical_xor(B+b,qctrl({a}));Q[b]=xx(Q[b],aa(k,Q[a]));break;
   case 49:classical_xor(B+t,qctrl({a,b}));Q[t]=xx(Q[t],aa(k,aa(Q[a],Q[b])));break;
   case 34:case 50:{U u=op==34?a:b,v=op==34?b:t;int f=op==34?k:aa(k,Q[a]);bool sub=op==50&&Q[a]==2;if(sub)push(B+a);cbx(B+u,B+v);cbx(B+v,B+u);cbx(B+u,B+v);if(sub)pop();int x=Q[u],y=Q[v];Q[u]=assign3(x,y,f);Q[v]=assign3(y,x,f);break;}
  }
  if(cond)pop();shadow_ops+=w.ops.size()-n-1;mirrored++;
 }
 if(active.size()!=1)throw runtime_error("unbalanced scope");
 // 31 retained flags, 29 chain scratch. Recompute each erased product
 // only for its actual nonzero classical HMR result.
 const U groups=31;
 push(debt);
 for(U q:guardS)emit(17,q);
 auto ccx=[&](U a,U b,U c){emit(49,a,b,c);};
 auto erase=[&](U a,U b,U p){emit(80,p,0,0,undo);emit(160,a,b,0,0,undo);};
 auto build=[&](vector<U> const&v,U target,bool include_target){
   assert(v.size()>=3&&groups+v.size()-3<work.size());
   ccx(v[0],v[1],work[groups]);for(size_t j=2;j+1<v.size();j++)ccx(work[groups+j-2],v[j],work[groups+j-1]);
   if(include_target)ccx(work[groups+v.size()-3],v.back(),target);
 };
 auto cleanup=[&](vector<U> const&v,U target,bool include_target){
   if(include_target)erase(work[groups+v.size()-3],v.back(),target);
   for(int j=int(v.size())-2;j>=2;j--)erase(work[groups+j-2],v[j],work[groups+j-1]);erase(v[0],v[1],work[groups]);
 };
 vector<vector<U>> blocks;
 for(U j=0;j<groups;j++){
   U lo=420*j/groups,hi=420*(j+1)/groups;blocks.emplace_back(guardS.begin()+lo,guardS.begin()+hi);
   build(blocks.back(),work[j],true);cleanup(blocks.back(),work[j],false);
 }
 vector<U> flags(work.begin(),work.begin()+groups);
 build(flags,0,false);emit(32,work[groups+flags.size()-3],flags.back());cleanup(flags,0,false);
 for(int j=int(groups)-1;j>=0;j--){
   emit(80,work[j],0,0,flagdraw);push(flagdraw);
   auto &v=blocks[j];build(v,0,false);emit(32,work[groups+v.size()-3],v.back());cleanup(v,0,false);
   pop();clear(flagdraw);
 }
 for(U q:guardS)emit(17,q);pop();
 for(U q=0;q<r.Q;q++)clear(B+q);clear(debt);clear(draw);clear(undo);clear(flagdraw);
 w.write(argv[2]);cerr<<"original_ops "<<r.counts[0]<<" new_ops "<<w.ops.size()<<" original_paid "<<r.counts[1]<<" new_paid "<<w.a[2].size()<<" mirror "<<mirrored<<" shadow_ops "<<shadow_ops<<" converted_R "<<converted<<"\n";
}
