#include "native.hpp"
#include <bitset>
using V=bitset<841>;
int main(int argc,char**argv){Reader r(argv[1]);vector<V> q(r.Q);for(auto p:r.regs){U n,l;memcpy(&n,p.ptr,4);memcpy(&l,p.ptr+4,4);if(p.ptr[8]!='S')continue;U j=stoul(string(p.ptr+9,n-1));assert(j<70&&l==12);for(U k=0;k<12;k++){U x;memcpy(&x,p.ptr+8+n+4*k,4);q[x&0x7fffffff].set(12*j+k);}}
 int depth=0;L affine=0,condValue=0;for(L i=0;i<r.counts[0];i++){auto g=r.read(i);int op=g.op&127;if(g.op==129){depth++;continue;}if(op==1){depth--;continue;}if(op==49||op==50||op==80||op==18){cerr<<"FIRST nonlinear "<<i<<" op "<<op<<" a "<<g.a<<" b "<<g.b<<" t "<<g.t<<" depth "<<depth<<" affine "<<affine<<" conditional "<<condValue<<endl;ofstream f(argv[2]);f<<i<<' '<<g.a<<' '<<g.b<<' '<<g.t<<'\n';for(auto const&v:q)f<<v.to_string()<<'\n';return condValue?2:0;}
 if(op==17||op==33||op==34){affine++;if(g.op&128)condValue++;if(op==17)q[g.a].flip(840);else if(op==33)q[g.b]^=q[g.a];else swap(q[g.a],q[g.b]);}
 }return 3;}

