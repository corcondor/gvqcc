#include "native.hpp"
#include <sstream>
bool eq(Gate x,Gate y){return x.op==y.op&&x.a==y.a&&x.b==y.b&&x.t==y.t&&x.bit==y.bit&&x.cond==y.cond;}
vector<Gate> gates(const string& path){
    Reader r(path); vector<Gate> g;
    for(L i=0;i<r.counts[0];++i)g.push_back(r.read(i));
    assert(!g.empty()); return g;
}
int main(int argc,char** argv){
    assert(argc==11);
    Reader r(argv[1]);
    vector<vector<Gate>> a,b;
    vector<vector<size_t>> prefix;
    for(int i=3;i<argc;i+=2){
        a.push_back(gates(argv[i])); b.push_back(gates(argv[i+1]));
        auto& g=a.back(); vector<size_t> p(g.size());
        for(size_t j=1,k=0;j<g.size();++j){while(k&&!eq(g[k],g[j]))k=p[k-1];p[j]=k+=eq(g[k],g[j]);}
        prefix.push_back(p);
    }
    map<L,int> hits;
    vector<int> counts(a.size()); vector<size_t> k(a.size());
    for(L i=0;i<r.counts[0];++i){
        auto g=r.read(i);
        for(size_t j=0;j<a.size();++j){
            while(k[j]&&!eq(a[j][k[j]],g))k[j]=prefix[j][k[j]-1];
            k[j]+=eq(a[j][k[j]],g);
            if(k[j]==a[j].size()){
                assert(hits.emplace(i+1-k[j],j).second);
                ++counts[j]; k[j]=prefix[j].back();
            }
        }
    }
    bool all=true;
    for(size_t j=0;j<a.size();++j){cout<<j<<' '<<counts[j]<<' '<<a[j].size()<<' '<<b[j].size()<<endl;all&=counts[j]==1;}
    if(!all)return 2;
    r.reset();
    Writer w(r,r.B);
    for(L i=0;i<r.counts[0];){
        auto f=hits.find(i);
        if(f==hits.end()){w.put(r.read(i++));continue;}
        int j=f->second;
        cout<<"offset "<<i<<" component "<<j<<endl;
        for(auto op:a[j]){assert(eq(op,r.read(i)));++i;}
        for(auto op:b[j])w.put(op);
    }
    w.write(argv[2]); cout<<"ops "<<w.ops.size()<<endl;
}
