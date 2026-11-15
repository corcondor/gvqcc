// Numerical forward-path probe, NOT a reversible submitted circuit.
// Extracts exact Boolean rotation predicates from the pinned e46 KMX stream.
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using U = std::uint64_t;
struct Op { int t,a,b,c; };
template<class T> std::vector<T> read_file(const std::string &p) {
    std::ifstream f(p,std::ios::binary|std::ios::ate);
    if(!f) throw std::runtime_error("cannot open "+p);
    const auto n=f.tellg(); f.seekg(0); std::vector<T> v(std::size_t(n)/sizeof(T));
    f.read(reinterpret_cast<char*>(v.data()),n); return v;
}
template<class T> void write_file(const std::string &p,const std::vector<T>&v) {
    std::ofstream f(p,std::ios::binary);
    f.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(T));
    if(!f) throw std::runtime_error("cannot write "+p);
}
int main(int argc,char **argv) {
    if(argc<7) throw std::runtime_error("ops base_D new_D output_prefix num_basis xs_or_all");
    std::vector<Op> ops; Op o; std::ifstream fi(argv[1]);
    while(fi>>o.t>>o.a>>o.b>>o.c) ops.push_back(o);
    auto oldD=read_file<std::uint16_t>(argv[2]); auto newD=read_file<std::uint16_t>(argv[3]);
    if(oldD.size()!=4096 || newD.size()!=4096) throw std::runtime_error("D table shape");
    std::vector<std::uint32_t> xs;
    if(std::string(argv[6])=="all") { xs.resize(3133452); for(std::size_t i=0;i<xs.size();++i) xs[i]=i+1; }
    else xs=read_file<std::uint32_t>(argv[6]);
    const std::size_t n=xs.size(), nw=(n+63)/64; const int nb=std::stoi(argv[5]);
    std::vector<U> bits(std::size_t(nb)*nw); std::vector<std::uint16_t> roots(n);
    const int D[13]={34,36,30,32,28,35,33,31,29,26,27,37,38};
    std::uint64_t mismatches=0, first_bad=0;
    for(std::size_t w=0;w<nw;++w) {
        U q[46]={}, phase=0; unsigned v[64]={};
        for(int l=0;l<64 && 64*w+l<n;++l) for(int j=0;j<22;++j) q[j]|=U((xs[64*w+l]>>j)&1)<<l;
        for(auto op:ops) switch(op.t) {
          case 0:q[op.a]=~q[op.a];break;
          case 1:q[op.b]^=q[op.a];break;
          case 2:q[op.c]^=q[op.a]&q[op.b];break;
          case 3:{U t=q[op.a];q[op.a]=q[op.b];q[op.b]=t;break;}
          case 4:{U t=q[op.a]&(q[op.b]^q[op.c]);q[op.b]^=t;q[op.c]^=t;break;}
          case 5:q[op.a]=0;break;
          case 6:phase^=q[op.a];break;
          case 7:phase^=q[op.a]&q[op.b];break;
          case 8:phase^=q[op.a]&q[op.b]&q[op.c];break;
          case 9:phase=~phase;break;
          case 10:bits[std::size_t(op.b)*nw+w]=q[op.a];break;
          case 12:
            for(int l=0;l<64 && 64*w+l<n;++l) {
                for(int j=0;j<12;++j) v[l]|=((q[10+j]>>l)&1)<<j;
                roots[64*w+l]=v[l];
            }
            break;
          case 13: {
            U replacement[13]={};
            for(int l=0;l<64 && 64*w+l<n;++l) {
                unsigned actual=0;
                for(int j=0;j<13;++j) actual|=((q[D[j]]>>l)&1)<<j;
                if(actual!=oldD[v[l]]) { ++mismatches; if(!first_bad)first_bad=xs[64*w+l]; }
                for(int j=0;j<13;++j) replacement[j]|=U((newD[v[l]]>>j)&1)<<l;
            }
            for(int j=0;j<13;++j) q[D[j]]=replacement[j];
            break;
          }
          default:throw std::runtime_error("unsupported opcode");
        }
        bits[std::size_t(nb-1)*nw+w]=phase;
    }
    const std::string prefix=argv[4];
    write_file(prefix+".basis.u64",bits);write_file(prefix+".roots.u16",roots);
    std::cout<<"{\"inputs\":"<<n<<",\"basis\":"<<nb<<",\"base_D_mismatches\":"<<mismatches
             <<",\"first_bad_x\":"<<first_bad<<"}"<<std::endl;
    return mismatches?2:0;
}
