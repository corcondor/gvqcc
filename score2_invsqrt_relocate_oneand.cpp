// Search one-AND phase predicates at different live cuts, using packed samples.
// Positive models require separate full-domain verification by the Python bridge.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <set>
#include <vector>
using U=uint64_t;
static int NW=8;
struct V{std::array<U,16>w;};
V zero(){V a{};return a;}
V xx(V a,const V&b){for(int i=0;i<NW;++i)a.w[i]^=b.w[i];return a;}
V aa(V a,const V&b){for(int i=0;i<NW;++i)a.w[i]&=b.w[i];return a;}
int top(const V&a){for(int i=NW-1;i>=0;--i)if(a.w[i])return i*64+63-__builtin_clzll(a.w[i]);return -1;}
bool bit(const V&a,int p){return a.w[p/64]>>(p%64)&1;}
struct Basis{
 std::array<int,1024> index;std::array<V,64> v;std::array<U,64> c;std::array<int,64> order;int rank=0;
 Basis(){index.fill(-1);}
 void add(V a,U co){int p;while((p=top(a))>=0){int j=index[p];if(j<0){j=rank;index[p]=j;v[j]=a;c[j]=co;int k=rank++;while(k>0&&order[k-1]<p){order[k]=order[k-1];--k;}order[k]=p;return;}a=xx(a,v[j]);co^=c[j];}}
 V quotient(V a)const{for(int i=0;i<rank;++i){int p=order[i];if(bit(a,p))a=xx(a,v[index[p]]);}return a;}
 bool solve(V a,U&co)const{co=0;int p;while((p=top(a))>=0){int j=index[p];if(j<0)return false;a=xx(a,v[j]);co^=c[j];}return true;}
};
V eval(U mask,const std::array<V,46>&v){V a=zero();while(mask){int i=__builtin_ctzll(mask);a=xx(a,v[i]);mask&=mask-1;}return a;}
int main(int argc,char**argv){
 if(argc<2)return 2;std::ifstream f(argv[1]);int ncuts,nt;f>>NW>>ncuts>>nt;if(NW>16)return 3;
 V one=zero();for(int j=0;j<NW;++j)f>>one.w[j];std::vector<V>target(nt);std::vector<int>start(nt),end(nt);
 for(int t=0;t<nt;++t){f>>start[t]>>end[t];target[t]=zero();for(int j=0;j<NW;++j)f>>target[t].w[j];}
 std::set<U>leftset;for(int i=0;i<46;++i){leftset.insert(U(1)<<i);for(int j=0;j<i;++j)leftset.insert((U(1)<<i)|(U(1)<<j));}
 int flags[5]={22,23,24,25,7};for(unsigned mask=0;mask<32;++mask){U flag=0;for(int j=0;j<5;++j)if(mask>>j&1)flag^=U(1)<<flags[j];if(flag)leftset.insert(flag);for(int q=0;q<46;++q)if(flag!=(U(1)<<q))leftset.insert(flag^(U(1)<<q));}
 std::vector<U>lefts(leftset.begin(),leftset.end());auto began=std::chrono::steady_clock::now();long long queries=0;
 for(int cutno=0;cutno<ncuts;++cutno){int cut;U zeros;f>>cut>>zeros;std::array<V,46>v;for(V &a:v){a=zero();for(int j=0;j<NW;++j)f>>a.w[j];}
   Basis lin;lin.add(one,1);for(int q=0;q<46;++q)lin.add(v[q],U(1)<<(q+1));
   std::vector<V>res(nt);for(int t=0;t<nt;++t)res[t]=lin.quotient(target[t]);
   std::array<std::array<V,46>,46>m;for(int i=0;i<46;++i){m[i][i]=zero();for(int j=0;j<i;++j)m[i][j]=m[j][i]=lin.quotient(aa(v[i],v[j]));}
   for(U left:lefts){V av=eval(left,v);if(top(av)<0)continue;Basis product;
     for(int j=0;j<46;++j){V col=zero();U mask=left;while(mask){int i=__builtin_ctzll(mask);col=xx(col,m[i][j]);mask&=mask-1;}product.add(col,U(1)<<j);}
     for(int t=0;t<nt;++t){if(start[t]<=cut&&cut<=end[t])continue;++queries;U right;if(!product.solve(res[t],right))continue;
       V bv=eval(right,v);U linear;if(!lin.solve(xx(target[t],aa(av,bv)),linear))return 4;
       std::cout<<"{\"status\":\"SAMPLE_MODEL\",\"target_index\":"<<t<<",\"cut\":"<<cut<<",\"zero_qubits_mask\":"<<zeros<<",\"left_mask\":"<<left<<",\"right_mask\":"<<right<<",\"affine_mask_constant_then_qubits\":"<<linear<<",\"queries\":"<<queries<<",\"cut_index\":"<<cutno<<"}\n";return 0;
     }
   }
   if(cutno%10==0){double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count();std::cerr<<"{\"cut_index\":"<<cutno<<",\"cuts\":"<<ncuts<<",\"queries\":"<<queries<<",\"seconds\":"<<sec<<"}\n"<<std::flush;if(sec>180){std::cout<<"{\"status\":\"TIME_LIMIT\",\"cut_index\":"<<cutno<<",\"cuts\":"<<ncuts<<",\"queries\":"<<queries<<"}\n";return 0;}}
 }
 std::cout<<"{\"status\":\"NO_MODEL_IN_SEARCHED_LEFT_FAMILY\",\"cuts\":"<<ncuts<<",\"queries\":"<<queries<<",\"left_parities\":"<<lefts.size()<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count()<<"}\n";
}
