#include "native.hpp"
int main(int argc,char** argv){
 Reader r(argv[1]); ifstream in(argv[3]); string line; vector<L> starts;
 while(getline(in,line))if(line[0]=='#')starts.push_back(stoull(line.substr(2)));
 Writer w(r,r.B); size_t j=0;
 for(L i=0;i<r.counts[0];i++){
  if(j<starts.size()&&i==starts[j]){
    w.put(Gate{50,0,r.Q,r.Q+1});
    ++j;
  }
  w.put(r.read(i));
 }
 assert(j==starts.size());
 r.Q+=2; w.write(argv[2]);
}
