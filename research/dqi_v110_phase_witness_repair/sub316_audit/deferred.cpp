#include "../other/src/native.hpp"
#include <map>
struct Cand {L i,frame,va,vb;U a,b;};
struct Debt {U a,b,m;};
int main(int argc,char**argv){
 if(argc!=2&&argc!=3)return 2;
 Reader r(argv[1]);
 vector<L> epoch(r.Q); vector<vector<Cand>> keep(r.Q);
 vector<L> frames={0}; map<L,vector<Debt>> debts; std::set<L> del;
 L eligible=0, groups=0;
 for(L i=0;i<r.counts[0];++i){
   Gate g=r.read(i);const int op=g.op&127;
   if(g.op==129){frames.push_back(i+1);continue;}
   if(op==1){assert(frames.size()>1);frames.pop_back();continue;}
   auto a=g.a,b=g.b,t=g.t;
   auto use=[&](U q){keep.at(q).clear();};
   auto set=[&](U q){++epoch.at(q); use(q);};
   switch(op){
     case 0x00:case 0x40:case 0x41:case 0x42:break;
     case 0x10:use(a);break;
     case 0x11:++epoch[a];break;
     case 0x12:set(a);break;
     case 0x20:use(a);use(b);break;
     case 0x21:use(a);++epoch[b];break;
     case 0x22:set(a);set(b);break;
     case 0x30:use(a);use(b);use(t);break;
     case 0x31:
       assert(a!=b&&a!=t&&b!=t);
       use(a);use(b);++epoch[t];
       if(g.op==0x31){keep[t].push_back({i,frames.back(),epoch[a],epoch[b],a,b});++eligible;}
       break;
     case 0x32:use(a);set(b);set(t);break;
     case 0x50:
       if(g.op==0x50){
         for(auto h:keep[a])if(h.frame==frames.back()&&h.va==epoch[h.a]&&h.vb==epoch[h.b]){
           del.insert(h.i);debts[i].push_back({h.a,h.b,g.bit});
         }
         if(debts.count(i))++groups;
       }
       set(a);break;
     default: cerr<<"unknown op "<<op<<" at "<<i<<endl;return 3;
   }
 }
 assert(frames.size()==1);
 cerr<<"eligible "<<eligible<<" exact HMR debts "<<groups<<" paid removed "<<del.size()<<endl;
 if(argc==2||del.empty())return 0;
 Writer w(r,r.B);r.reset();ofstream report(string(argv[2])+".tsv");
 for(L i=0;i<r.counts[0];i++){
   auto g=r.read(i);
   if(del.count(i)){report<<"drop\t"<<i<<'\t'<<g.a<<'\t'<<g.b<<'\t'<<g.t<<'\n';continue;}
   w.put(g);auto it=debts.find(i);if(it!=debts.end())for(auto z:it->second){
     w.put(Gate{0xa0,z.a,z.b,0,0,z.m});
     report<<"debt\t"<<i<<'\t'<<z.a<<'\t'<<z.b<<'\t'<<z.m<<'\n';
   }
 }
 assert(w.a[2].size()+del.size()==r.counts[1]);w.write(argv[2]);
}
