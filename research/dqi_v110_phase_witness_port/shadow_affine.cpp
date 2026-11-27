#include "kmb.hpp"
#include "abstract.hpp"
#include "paid_pairs.hpp"
// Reuse the classical phase replay, with identical actual measurement outcomes.
// The added diagonal correction is limited to the restored zero syndrome.
struct Emit {
 vector<uint8_t> op; vector<I> c[10];
 void g(int t,int a=-1,int b=-1,int d=-1,I m=0,I k=0){op.push_back(t);switch((t>>4)&3){case 1:c[7].push_back(a);break;case 2:c[5].push_back(a);c[6].push_back(b);break;case 3:c[2].push_back(a);c[3].push_back(b);c[4].push_back(d);break;}if(t&64)c[8].push_back(m);if(t&128)c[9].push_back(k);}
 void orig(G v,int t=-1){g(t<0?v.t:t,v.a,v.b,v.c,v.m,v.k);}
 void push(I b){g(129,-1,-1,-1,0,b);}void pop(){g(1);}
 void bx(I a,int b=-1){if(b<0)g(66,-1,-1,-1,a);else g(194,-1,-1,-1,a,b);}
 void reset(I a,int v=0){g(64+v,-1,-1,-1,a);}
 void swapb(I a,I b){if(a!=b){bx(a,b);bx(b,a);bx(a,b);}}
 void ccx(int a,int b,int t){g(49,a,b,t);}
 void erase_and(int a,int b,int t,I m){g(80,t,-1,-1,m);g(160,a,b,-1,0,m);}
};
int AND(int a,int b){return a==0||b==0?0:a==1&&b==1?1:2;}
int XOR(int a,int b){return a==2||b==2?2:a^b;}
int MERGE(int a,int b,int f){return f==0||a==b?a:f==1?b:2;}
void word(ofstream&f,U k,U n,const void*p){f.write((char*)&k,8);f.write((char*)&n,8);if(n)f.write((const char*)p,n);}
// Reuse division.py::zero_flag/phase_zero, in raw native opcodes.
void product_flag(Emit&e,const vector<int>&x,const vector<int>&scratch,int dst,I m){assert(x.size()>=2&&scratch.size()>=x.size()-2);vector<int> v(scratch.begin(),scratch.begin()+x.size()-2);v.push_back(dst);for(size_t i=0;i<v.size();i++)e.ccx(i?v[i-1]:x[0],x[i+1],v[i]);for(int i=int(v.size())-2;i>=0;i--)e.erase_and(i?v[i-1]:x[0],x[i+1],v[i],m);}
void product_phase(Emit&e,const vector<int>&x,const vector<int>&scratch,I m){assert(x.size()>=2&&scratch.size()>=x.size()-2);int n=x.size()-2;for(int i=0;i<n;i++)e.ccx(i?scratch[i-1]:x[0],x[i+1],scratch[i]);e.g(32,n?scratch[n-1]:x[0],x.back());for(int i=n-1;i>=0;i--)e.erase_and(i?scratch[i-1]:x[0],x[i+1],scratch[i],m);}
int main(int argc,char**argv){assert(argc==6 || argc==7); int guard_words=stoi(argv[5]);assert(guard_words==35 || guard_words==70); int groups_n=argc==7?stoi(argv[6]):31;assert(groups_n==28 || groups_n==31);K k(argv[1]);ifstream ss(argv[2]);vector<int>S;int j;while(ss>>j)S.push_back(j);assert(S.size()==840);set<int> si(S.begin(),S.end());assert(si.size()==840);vector<int> anc;for(int j=0;j<k.Q;j++)if(!si.count(j))anc.push_back(j);assert(anc.size()>=58);
 ifstream mm(argv[3]);vector<int>C(k.B,0);Abstract A(k.Q);auto &Q=A.q;auto &st=A.st;while(mm>>j)C.at(j)=2;I B=k.B,P=B+k.Q,M=P+1, R=M+2;auto skip=paid_pairs(k);Emit e;e.op.reserve(k.N+30000000);for(int j=2;j<=9;j++)e.c[j].reserve(k.len[j]/4+(j>=8?16000000:100));
 for(int q=0;q<k.Q;q++)e.reset(B+q);e.reset(P);e.reset(M);e.reset(R);U mirror=0, lifted=0;int depth=0;
 for(I i=0;i<k.N;i++){if(A.n>MAX-20)A.rebase();G v=k.next(i);if(skip[i])continue;int t=v.t,op=t&127;V f=st.back();if(t==129){e.orig(v);st.push_back(A.andp(f,A.bit(v.k,C.at(v.k))));depth++;continue;}if(t==1){e.orig(v);st.pop_back();depth--;continue;}if(t&128)f=A.andp(f,A.bit(v.k,C.at(v.k)));
 int fk=A.known(f);
 if(op>=64&&op<=66){e.orig(v);int old=C.at(v.m);int val=op==64?0:op==65?1:XOR(old,1);C.at(v.m)=MERGE(old,val,fk);if(fk!=0)A.invalidate(v.m);continue;}
 bool cond=t&128;if(cond)e.push(v.k);bool lift = op==18 && A.andp(f,Q.at(v.a)).any(); if(lift){e.g(80,v.a,-1,-1,R);lifted++;}else e.orig(v,op);size_t prev=e.op.size();
 auto toggle=[&](int q,initializer_list<int> controls){V a=f;for(int c:controls)a=A.andp(a,Q.at(c));if(a.any()){int n=0;for(int c:controls)if(A.known(Q[c])==2){e.push(B+c);n++;}e.bx(B+q);while(n--)e.pop();}Q[q]^=a;};
 auto phase=[&](initializer_list<int> controls,int bit=-1){V a=f;for(int c:controls)a=A.andp(a,Q.at(c));if(bit>=0)a=A.andp(a,A.bit(bit,C.at(bit)));if(a.none())return;int n=0;for(int c:controls)if(A.known(Q[c])==2){e.push(B+c);n++;}if(bit>=0&&C[bit]==2){e.push(bit);n++;}e.bx(P);while(n--)e.pop();};
 auto sw=[&](int a,int b,int c=-1){V F=c<0?f:A.andp(f,Q.at(c)),z=A.andp(F,Q.at(a)^Q.at(b));if(z.none())return;int qa=A.known(Q[a]),qb=A.known(Q[b]);if(c>=0&&A.known(Q[c])==2)e.push(B+c);if(qa<2&&qb<2&&qa!=qb){e.bx(B+a);e.bx(B+b);}else e.swapb(B+a,B+b);if(c>=0&&A.known(Q[c])==2)e.pop();Q[a]^=z;Q[b]^=z;};
 switch(op){case 0:phase({});break;case 16:phase({v.a});break;case 17:toggle(v.a,{});break;case 18:{V z=A.andp(f,Q[v.a]);if(z.any()){assert(lift);e.push(R);phase({v.a});e.pop();e.reset(B+v.a);}Q[v.a]^=z;break;}case 32:phase({v.a,v.b});break;case 33:toggle(v.b,{v.a});break;case 34:sw(v.a,v.b);break;case 48:phase({v.a,v.b,v.c});break;case 49:toggle(v.c,{v.a,v.b});break;case 50:sw(v.b,v.c,v.a);break;case 80:{C[v.m]=MERGE(C[v.m],2,fk);if(fk!=0)A.invalidate(v.m);phase({v.a},v.m);V z=A.andp(f,Q[v.a]);if(z.any())e.reset(B+v.a);Q[v.a]^=z;break;}default:cerr<<"bad "<<op<<" at "<<i<<endl;return 2;}
 mirror+=e.op.size()-prev;if(cond){if(e.op.size()==prev){assert(e.op[prev-2]==129&&e.op[prev-1]==op);e.op.pop_back();e.op.back()=t;}else e.pop();}}
 assert(depth==0);cerr<<"mirror "<<mirror<<" ref unknown final "<<count_if(Q.begin(),Q.end(),[&](V x){return A.known(x)==2;})<<" ref nonzero final "<<count(Q.begin(),Q.end(),A.one)<<" lifted_R "<<lifted<<" rebases "<<A.rebases<<"\n";
 // On legal <=35-sparse restored inputs, the first 35 moments determine
 // whether the syndrome is zero (Vandermonde, using the original S register order).
 // For arbitrary returned words, only the full scan implements exact output
 // zero. Even a full scan is not an input-zero proof if restoration can fail.
 S.resize(12*guard_words);

 e.push(P);for(int q:S)e.g(17,q);vector<int> flags(anc.begin(),anc.begin()+groups_n),work(anc.begin()+groups_n,anc.end());vector<vector<int>> groups;
 for(int g=0;g<groups_n;g++){groups.emplace_back(S.begin()+S.size()*g/groups_n,S.begin()+S.size()*(g+1)/groups_n);product_flag(e,groups.back(),work,flags[g],M);}product_phase(e,flags,work,M);
 I m2=M+1;for(int g=groups_n-1;g>=0;g--){e.g(80,flags[g],-1,-1,m2);e.push(m2);product_phase(e,groups[g],work,M);e.pop();}
 for(int q:S)e.g(17,q);e.pop();for(int j=0;j<k.Q;j++)e.reset(B+j);e.reset(P);e.reset(M);e.reset(m2);e.reset(R);
 ofstream out(argv[4],ios::binary);out.write((char*)k.p,16);I h[4];memcpy(h,k.p+16,16);h[2]=R+1;out.write((char*)h,16);U h2[9]={e.op.size(),e.c[2].size(),e.c[5].size(),e.c[7].size(),e.c[8].size(),e.c[9].size(),0,0,0};out.write((char*)h2,72);for(auto s:k.sections)if(!s.k)word(out,s.k,s.n,s.p);word(out,1,e.op.size(),e.op.data());for(int j=2;j<=9;j++)word(out,j,e.c[j].size()*4,e.c[j].data());for(auto s:k.sections)if(s.k>=10)word(out,s.k,s.n,s.p);cerr<<"Q "<<h[1]<<" B "<<h[2]<<" ops "<<h2[0]<<" threeq "<<h2[1]<<"\n";
}
