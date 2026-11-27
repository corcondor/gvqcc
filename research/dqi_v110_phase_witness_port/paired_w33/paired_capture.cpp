#include "common.hpp"
// Add two bits per measurement site: whether it ran, and its sampled outcome.
// Inline classical predicates are kept around the recorded sub-block.
int main(int argc,char**argv){
 assert(argc==3);
 Reader r(argv[1]);U H=0;
 for(L i=0;i<r.counts[0];i++){auto g=r.read(i);H+=((g.op&127)==18||(g.op&127)==80);}r.reset();
 Writer w(r,r.B+2*H);U m=0;
 for(L i=0;i<r.counts[0];i++){
   auto g=r.read(i);int op=g.op&127;
   if(op!=18 && op!=80){w.put(g);continue;}
   U active=r.B+2*m++,sample=active+1;
   bool guard=g.op&128;
   if(guard){Gate p{};p.op=129;p.cond=g.cond;w.put(p);}
   g.op=80;if(op==18)g.bit=sample;
   w.put(g);
   Gate a{};a.op=65;a.bit=active;w.put(a);
   if(op==80){Gate h{};h.op=194;h.bit=sample;h.cond=g.bit;w.put(h);}
   if(guard){Gate p{};p.op=1;w.put(p);}
 }
 assert(m==H);w.write(argv[2]);cout<<r.B<<" "<<H<<"\n";
}
