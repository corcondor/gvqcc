#include "native.hpp"
int main(int argc,char** argv) {
 Reader r(argv[1]); L a=stoull(argv[2]), b=stoull(argv[3]);vector<U> scope;
 for(L i=0;i<b;++i){ auto g=r.read(i);
 if(i==a){cerr<<"guards:";for(auto t:scope)cerr<<" "<<t;cerr<<"\n";}
 if(i>=a) cout<<i<<" "<<(int)g.op<<" "<<g.a<<" "<<g.b<<" "<<g.t<<" "<<g.bit<<" "<<g.cond<<"\n";
 if((g.op&127)==1 && (g.op&128))scope.push_back(g.cond);
 if(g.op==1){assert(!scope.empty());scope.pop_back();}
 }
}
