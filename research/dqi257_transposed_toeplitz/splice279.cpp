#include "common.hpp"
#pragma pack(push,1)
struct Classical{uint8_t op;U bit,cond;};
#pragma pack(pop)
vector<Classical> load(const char*name){ifstream f(name,ios::binary|ios::ate);assert(f);L n=f.tellg();assert(n%sizeof(Classical)==0);vector<Classical> v(n/sizeof(Classical));f.seekg(0);f.read((char*)v.data(),n);assert(f);return v;}
bool eq(Gate const&g,Classical const&c){return g.op==c.op&&g.bit==c.bit&&g.cond==c.cond;}
int main(int argc,char**argv){assert(argc==5);Reader r(argv[1]);auto old=load(argv[2]),nw=load(argv[3]);L found=0,match=0;L start=0;for(L i=0;i<r.counts[0];i++){auto g=r.read(i);if(eq(g,old[match])){if(!match)start=i;match++;if(match==old.size()){found++;cerr<<"match "<<start<<" "<<i+1<<endl;break;}}else{match=0;if(eq(g,old[0])){start=i;match=1;}}}assert(found==1);r.reset();U maxB=r.B;for(auto g:nw){maxB=max(maxB,g.bit+1);maxB=max(maxB,g.cond+1);}Writer w(r,maxB);for(L i=0;i<r.counts[0];i++){auto g=r.read(i);if(i==start)for(auto c:nw)w.put({c.op,0,0,0,c.bit,c.cond});if(i<start||i>=start+old.size())w.put(g);}w.write(argv[4]);cerr<<"ops "<<w.ops.size()<<" paid "<<w.a[2].size()<<" B "<<maxB<<endl;}
