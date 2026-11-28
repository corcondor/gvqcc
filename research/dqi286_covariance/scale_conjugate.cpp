#include "native.hpp"
// Public mask permutation corresponds to physical multiplication by primitive alpha=2.
int main(int argc,char**argv){assert(argc==4);Reader r(argv[1]);assert(r.Q==900&&r.B>=49140);ifstream f(argv[2]);vector<Gate>v;unsigned op;U a,b;while(f>>op>>a>>b){assert(op==33||op==34);v.push_back({(unsigned char)op,a,b});}assert(!v.empty());Writer w(r,r.B);for(auto g:v)w.put(g);
 auto perm=[](U x){U q=x&0x7fffffff;if(q<49140)q=((q/12+4094)%4095)*12+q%12;return q|(x&0x80000000);};
 for(L i=0;i<r.counts[0];i++){auto g=r.read(i);int base=g.op&127;if((g.op&64)&&base!=6&&base!=7)g.bit=perm(g.bit);if(g.op&128)g.cond=perm(g.cond);w.put(g);}
 for(auto i=v.rbegin();i!=v.rend();++i)w.put(*i);w.write(argv[3]);cout<<"old "<<r.counts[0]<<" new "<<w.ops.size()<<" frame "<<v.size()<<" paid "<<w.a[2].size()<<endl;}
