#include "../other/src/native.hpp"
#include <optional>
struct C { L i, scope, av,bv; U a,b; unsigned paid=0; vector<pair<L,Gate>> obs; };
int main(int ac,char**argv){
 if(ac!=2&&ac!=3)return 2;
 Reader r(argv[1]);vector<L> ver(r.Q),f{0};
 vector<optional<C>> cand(r.Q);map<L,vector<Gate>> repl;
 L ccx=0,pairs=0,z=0,cz=0,net=0;
 for(L i=0;i<r.counts[0];i++){
  auto g=r.read(i);int op=g.op&127; U a=g.a,b=g.b,t=g.t;
  auto clear=[&](U x){cand.at(x).reset();};
  auto write=[&](U x){++ver.at(x);clear(x);};
  if(g.op==129){f.push_back(i+1);continue;}
  if(op==1){assert(f.size()>1);f.pop_back();continue;}
  auto phase=[&](U x,optional<U> v){
   auto& c=cand[x];if(!c)return;
   if(find(f.begin(),f.end(),c->scope)==f.end()){clear(x);return;}
   U p=c->a,q=c->b;
   Gate h{static_cast<unsigned char>((v&&*v!=p&&*v!=q?48:32)|(g.op&128)),p,q,v.value_or(0),0,g.cond};
   if(h.op&16)++c->paid;
   if(c->paid>1){clear(x);return;}
   c->obs.push_back({i,h});
  };
  switch(op){
   case 0:case 64:case 65:case 66:break;
   case 16:phase(a,nullopt);break;
   case 17:++ver[a];break;
   case 18:case 80:write(a);break;
   case 32:
      if(cand[a]&&cand[b]){clear(a);clear(b);}
      else {phase(a,b);phase(b,a);}break;
   case 33:clear(a);++ver[b];break;
   case 34:write(a);write(b);break;
   case 48:clear(a);clear(b);clear(t);break;
   case 49:{
      clear(a);clear(b);++ver[t];if(a>b)swap(a,b);
      auto& c=cand[t];
      if(g.op==49){
        ++ccx;
        if(c&&c->scope==f.back()&&c->a==a&&c->b==b&&c->av==ver[a]&&c->bv==ver[b]){
          // Need a saving also when the observer uses stricter guards; 2 removed,
          // at most 1 replacement paid if the original pair executes.
          assert(!repl.count(c->i)&&!repl.count(i));
          repl[c->i]={};repl[i]={};
          for(auto [j,h]:c->obs){assert(j<i);repl[j].push_back(h);(h.op&16?cz:z)++;}
          net+=2-c->paid;++pairs;clear(t);
        }else c=C{i,f.back(),ver[a],ver[b],a,b,0,{}};
      }
      break;
   }
   case 50:clear(a);write(b);write(t);break;
   default:cerr<<"unknown "<<op<<endl;return 3;
  }
 }
 assert(f.size()==1);
 cerr<<"CCX scanned "<<ccx<<" paired "<<pairs<<" phase CZ "<<z<<" phase CCZ "<<cz<<" static paid delta -"<<net<<endl;
 if(ac==2||!pairs)return 0;
 r.reset();Writer w(r,r.B);ofstream cert(string(argv[2])+".tsv");
 for(L i=0;i<r.counts[0];i++){
   auto g=r.read(i);auto it=repl.find(i);if(it==repl.end()){w.put(g);continue;}
   if(!it->second.empty())w.put(g);for(auto h:it->second)w.put(h);
   cert<<i<<'\t'<<int(g.op)<<'\t'<<it->second.size()<<'\n';
 }
 assert(r.counts[1]==w.a[2].size()+net);w.write(argv[2]);
}
