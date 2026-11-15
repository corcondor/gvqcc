#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
using namespace std;
static uint64_t le(const uint8_t* p, int n) {
    uint64_t value=0;
    for(int i=0;i<n;i++)value|=uint64_t(p[i])<<(8*i);
    return value;
}
struct Life {
    unsigned q;
    uint64_t first, stop, new_first, new_stop;
    bool abi;
};
struct Op {
    unsigned code, base, count;
    array<unsigned,3> qubits{};
    int64_t bit=-1, cond=-1;
};
struct Tape {
    int fd;
    const uint8_t* bytes;
    uint64_t size, nq, nb, n;
    array<uint64_t,12> p{}, end{};
    explicit Tape(const char* path) {
        fd=open(path,O_RDONLY);
        struct stat st;
        if(fd<0||fstat(fd,&st))throw runtime_error("open");
        size=st.st_size;
        bytes=static_cast<const uint8_t*>(mmap(nullptr,size,PROT_READ,MAP_PRIVATE,fd,0));
        if(bytes==MAP_FAILED||size<104||le(bytes+16,4)!=2)throw runtime_error("KMBv2 required");
        nq=le(bytes+20,4);
        nb=le(bytes+24,4);
        uint64_t nr=le(bytes+28,4), next=104;
        n=le(bytes+32,8);
        for(uint64_t i=0;i<nr+11;i++){
            if(next+16>size)throw runtime_error("packet");
            auto kind=le(bytes+next,8),length=le(bytes+next+8,8);
            next+=16;
            if(kind!=(i<nr?0:i-nr+1)||length>size-next)throw runtime_error("packet length");
            if(kind){p[kind]=next;end[kind]=next+length;}
            next+=length;
        }
        if(next!=size||end[1]-p[1]!=n)throw runtime_error("packet end");
    }
    uint64_t take(int c,int k) {
        if(p[c]+k>end[c])throw runtime_error("vector end");
        auto r=le(bytes+p[c],k);
        p[c]+=k;
        return r;
    }
    Op step() {
        Op o;
        o.code=take(1,1);o.base=o.code&127;o.count=(o.base>>4)&3;
        for(unsigned j=0;j<o.count;j++){
            o.qubits[j]=take(o.count==3?2+j:o.count==2?5+j:7,4);
            if(o.qubits[j]>=nq)throw runtime_error("qubit");
        }
        if(o.code&64)o.bit=take(8,4);
        if(o.code&128)o.cond=take(9,4);
        if(o.bit>=int64_t(nb)||o.cond>=int64_t(nb))throw runtime_error("bit");
        if(o.base==0x13){take(10,8);take(10,8);}
        return o;
    }
    ~Tape(){munmap(const_cast<uint8_t*>(bytes),size);close(fd);}
};

#include <cstring>
#include <utility>
#include <unordered_map>
#ifndef MAX_TERMS
#define MAX_TERMS 12
#endif
#ifndef MAX_DEGREE
#define MAX_DEGREE 4
#endif
static constexpr unsigned M=MAX_TERMS, D=MAX_DEGREE;
struct Mono {
    array<uint32_t,D> atoms{};
    bool operator<(const Mono &r) const {return atoms<r.atoms;}
    bool operator==(const Mono &r)const{return atoms==r.atoms;}
};
struct Poly {
    array<Mono,M> ms;
    unsigned n=0;
    bool operator==(const Poly& other)const{
        return n==other.n&&equal(ms.begin(),ms.begin()+n,other.ms.begin());
    }
};
static uint32_t seed_atom=0;
static Poly opaque(){ Poly p; p.n=1; p.ms[0]=Mono{{++seed_atom}};return p;}
static Poly one(){ Poly p; p.n=1;p.ms[0]=Mono{};return p;}
static Poly poly_xor(const Poly&a,const Poly&b){
    Poly d;
    unsigned i=0,j=0;
    while(i<a.n||j<b.n){
        if(i<a.n&&j<b.n&&a.ms[i]==b.ms[j]){i++;j++;continue;}
        if(d.n==M)return opaque();
        bool pick=i<a.n&&(j==b.n||a.ms[i]<b.ms[j]);
        d.ms[d.n++]=pick?a.ms[i++]:b.ms[j++];
    }
    return d;
}
static bool product(const Mono&a,const Mono&b,Mono&r){
    unsigned i=0,j=0,k=0;
    while((i<D&&a.atoms[i])||(j<D&&b.atoms[j])){
        if(k==D)return false;
        if(i<D&&j<D&&a.atoms[i]&&a.atoms[i]==b.atoms[j]){
            r.atoms[k++]=a.atoms[i++];j++;
        }else if(i<D&&a.atoms[i]&&(j==D||!b.atoms[j]||a.atoms[i]<b.atoms[j])){
            r.atoms[k++]=a.atoms[i++];
        }else r.atoms[k++]=b.atoms[j++];
    }
    return true;
}
static Poly times(const Poly&a,const Poly&b){
    if(a.n==0||b.n==0)return Poly{};
    if(a.n==1&&a.ms[0]==Mono{})return b;
    if(b.n==1&&b.ms[0]==Mono{})return a;
    if(a==b)return a;
    array<Mono,M*M> p{};
    unsigned k=0;
    for(unsigned i=0;i<a.n;i++)for(unsigned j=0;j<b.n;j++){
        if(!product(a.ms[i],b.ms[j],p[k++]))return opaque();
    }
    sort(p.begin(),p.begin()+k);
    Poly r;
    for(unsigned i=0;i<k;){
        unsigned j=i+1;
        while(j<k&&p[i]==p[j])j++;
        if((j-i)&1){if(r.n==M)return opaque();r.ms[r.n++]=p[i];}
        i=j;
    }
    return r;
}
static uint64_t xor_key(const Poly& p){
    uint64_t h=0x6a09e667f3bcc909ull;
    auto i=0u;
    if(p.n&&p.ms[0]==Mono{})++i;
    for(;i<p.n;i++){
        for(uint32_t a:p.ms[i].atoms){
            h^=a;
            h*=0xd6e8feb86659fd93ull;
            h^=h>>31;
        }
    }
    return h;
}
static bool eq_mod_constant(const Poly&a,const Poly&b){
    unsigned i=a.n&&a.ms[0]==Mono{},j=b.n&&b.ms[0]==Mono{};
    return a.n-i==b.n-j&&equal(a.ms.begin()+i,a.ms.begin()+a.n,b.ms.begin()+j);
}
struct Change {unsigned index;Poly old;uint64_t previous;};
struct Scope {vector<Change> writes;Poly guard;uint64_t serial;int64_t guard_bit;};
int main(int argc,char** argv) {try{
    if(argc!=3&&argc!=5)throw runtime_error("usage input.kmb hits.tsv [positions.txt ranks.tsv]");
    vector<uint64_t> positions;
    ofstream rank_output;
    if(argc==5){
        ifstream input(argv[3]);
        uint64_t value;
        while(input>>value)positions.push_back(value);
        if(!is_sorted(positions.begin(),positions.end()))throw runtime_error("bad positions");
        rank_output.open(argv[4]);
        rank_output<<"position\trank\tunknown\tdistinct\n";
    }
    auto next_position=positions.begin();
    Tape tape(argv[1]);
    if(tape.nq<840)throw runtime_error("qubit ABI");
    vector<Poly> q(tape.nq), b(tape.nb);
    for(unsigned k=0;k<840;k++)q[k]=opaque();
    vector<uint64_t> seen(tape.nq+tape.nb,0);
    vector<Scope> scope;
    auto save=[&](unsigned qindex,const Poly&old) {
        if(scope.empty())return;
        auto &s=scope.back();
        if(seen[qindex]==s.serial)return;
        s.writes.push_back({qindex,old,seen[qindex]});
        seen[qindex]=s.serial;
    };
    unordered_multimap<uint64_t,unsigned> by_form;
    vector<uint64_t> qkey(tape.nq);
    unsigned distinct=0, constant=0;
    auto remove=[&](unsigned wire){
        if(q[wire].n==0||q[wire]==one()){--constant;return;}
        uint64_t key=qkey[wire];
        auto [first,last]=by_form.equal_range(key);
        auto pos=last;
        bool duplicate=false;
        for(auto it=first;it!=last;++it){
            if(it->second==wire)pos=it;
            else if(eq_mod_constant(q[it->second],q[wire]))duplicate=true;
        }
        if(!duplicate)--distinct;
        if(pos==last)throw runtime_error("tracking map");
        by_form.erase(pos);
    };
    auto insert=[&](unsigned wire){
        if(q[wire].n==0||q[wire]==one()){++constant;return;}
        uint64_t key=qkey[wire]=xor_key(q[wire]);
        auto [first,last]=by_form.equal_range(key);
        bool duplicate=false;
        for(auto it=first;it!=last;++it){
            if(eq_mod_constant(q[it->second],q[wire]))duplicate=true;
        }
        if(!duplicate)++distinct;
        by_form.emplace(key,wire);
    };
    for(unsigned k=0;k<tape.nq;k++)insert(k);
    unsigned max_distinct=0,max_unknown=0;
    uint64_t max_distinct_count=0,max_unknown_count=0,first_distinct=0,first_unknown=0;
    auto report_rank=[&](uint64_t position){
        map<Mono,vector<Mono>> row_by_pivot;
        for(auto &p:q){
            auto start=p.n&&p.ms[0]==Mono{}?1u:0u;
            vector<Mono> row(p.ms.begin()+start,p.ms.begin()+p.n);
            while(!row.empty()){
                auto it=row_by_pivot.find(row.back());
                if(it==row_by_pivot.end()){row_by_pivot.emplace(row.back(),row);break;}
                vector<Mono> next;
                set_symmetric_difference(row.begin(),row.end(),it->second.begin(),
                                         it->second.end(),back_inserter(next));
                row=std::move(next);
            }
        }
        rank_output<<position<<'\t'<<row_by_pivot.size()<<'\t'<<(tape.nq-constant)<<'\t'<<distinct<<'\n';
    };
    auto observe=[&](uint64_t i) {
        unsigned unknown=tape.nq-constant;
        if(distinct>max_distinct){max_distinct=distinct;max_distinct_count=0;first_distinct=i;}
        if(distinct==max_distinct)++max_distinct_count;
        if(unknown>max_unknown){max_unknown=unknown;max_unknown_count=0;first_unknown=i;}
        if(unknown==max_unknown)++max_unknown_count;
    };
    auto equiv_one=one();
    ofstream out(argv[2]);
    out<<"op\ttype\tq0\tq1\tq2\treplacement\n";
    uint64_t count[3]{},scores[3]{},top[3]{}, serial=0;
    auto hit=[&](uint64_t i,const Op& o,int type,const char* repl){
        ++scores[type];
        if(scope.empty()&&o.cond<0)++top[type];
        out<<i<<'\t'<<o.base<<'\t'<<o.qubits[0]<<'\t'<<o.qubits[1]<<'\t'<<o.qubits[2]<<'\t'<<repl<<'\n';
    };
    auto writeq=[&](unsigned t,const Poly& d,const Poly& guard) {
        if(d.n==0||guard.n==0)return;
        save(t,q[t]);
        auto next=poly_xor(q[t],times(d,guard));
        remove(t);q[t]=next;insert(t);
    };
    auto writeb=[&](unsigned t,const Poly& v,const Poly& guard) {
        if(guard.n==0)return;
        save(t+tape.nq,b[t]);
        if(guard==equiv_one)b[t]=v;
        else b[t]=poly_xor(b[t],times(guard,poly_xor(v,b[t])));
    };
    for(uint64_t i=0;i<tape.n;i++){
        observe(i);
        if(next_position!=positions.end()&&i==*next_position){
            report_rank(i);
            ++next_position;
        }
        Op o=tape.step();
        auto [x,y,z]=o.qubits;
        Poly guard=o.cond<0?equiv_one:b[o.cond];
        if(o.code==0x81){
            scope.push_back(Scope{{},guard,++serial,o.cond});
            save(tape.nq+o.cond,b[o.cond]);
            b[o.cond]=equiv_one;
            continue;
        }
        if(o.code==0x01){
            if(scope.empty())throw runtime_error("unbalanced POP");
            auto s=std::move(scope.back());scope.pop_back();
            for(auto& c:s.writes) {
                seen[c.index]=c.previous;
                Poly &v=c.index<tape.nq?q[c.index]:b[c.index-tape.nq];
                save(c.index,c.old);
                if(c.index==tape.nq+s.guard_bit) {
                    // Boolean condition register may be changed inside a PUSH.
                    // Use old, unknown-safe joining unless it is still 1 in this arm.
                    if(v==equiv_one){v=c.old;continue;}
                }
                auto next=poly_xor(c.old,times(s.guard,poly_xor(c.old,v)));
                if(c.index<tape.nq)remove(c.index);
                v=next;
                if(c.index<tape.nq)insert(c.index);
            }
            continue;
        }
        switch(o.base){
            case 0x11:writeq(x,equiv_one,guard);break;
            case 0x21:writeq(y,q[x],guard);break;
            case 0x31: {
                ++count[0];
                auto p=times(q[x],q[y]);
                if(!p.n||!guard.n)hit(i,o,0,"DELETE");
                else if(p==equiv_one)hit(i,o,0,"X");
                else if(p==q[x])hit(i,o,0,"CX0");
                else if(p==q[y])hit(i,o,0,"CX1");
                writeq(z,p,guard);
                break;}
            case 0x30:{
                ++count[1];
                auto p01=times(q[x],q[y]),p=times(p01,q[z]);
                if(!p.n||!guard.n)hit(i,o,1,"DELETE");
                else if(p==equiv_one)hit(i,o,1,"NEG");
                else if(p==q[x])hit(i,o,1,"Z0");
                else if(p==q[y])hit(i,o,1,"Z1");
                else if(p==q[z])hit(i,o,1,"Z2");
                else if(p==p01)hit(i,o,1,"CZ01");
                else if(p==times(q[x],q[z]))hit(i,o,1,"CZ02");
                else if(p==times(q[y],q[z]))hit(i,o,1,"CZ12");
                break;}
            case 0x22:{
                auto p=times(poly_xor(q[x],q[y]),guard);
                writeq(x,p,equiv_one);writeq(y,p,equiv_one);break;}
            case 0x32:{
                ++count[2];
                auto p=times(q[x],poly_xor(q[y],q[z]));
                if(!p.n||!guard.n)hit(i,o,2,"DELETE");
                else if(q[x]==equiv_one)hit(i,o,2,"SWAP");
                writeq(y,p,guard);writeq(z,p,guard);break;}
            case 0x12:writeq(x,q[x],guard);break;
            case 0x50:writeq(x,q[x],guard);writeb(o.bit,opaque(),guard);break;
            case 0x40:writeb(o.bit,Poly{},guard);break;
            case 0x41:writeb(o.bit,equiv_one,guard);break;
            case 0x42:writeb(o.bit,poly_xor(b[o.bit],equiv_one),guard);break;
            case 0x00:case 0x06:case 0x07:case 0x10:case 0x13:case 0x17:case 0x20:case 0x47:break;
            default:throw runtime_error("unexpected opcode "+to_string(o.base));
        }
    }
    if(!scope.empty())throw runtime_error("unclosed PUSH");
    cout<<"{\"ops\":"<<tape.n<<",\"atoms\":"<<seed_atom<<",\"paid\":["<<count[0]<<','<<count[1]<<','<<count[2]<<"],\"hits\":["<<scores[0]<<','<<scores[1]<<','<<scores[2]<<"],\"top_level\":["<<top[0]<<','<<top[1]<<','<<top[2]<<"],\"maximum_distinct_nonconstant_mod_complement\":"<<max_distinct<<",\"max_distinct_positions\":"<<max_distinct_count<<",\"first_max_distinct\":"<<first_distinct<<",\"maximum_unknown\":"<<max_unknown<<",\"max_unknown_positions\":"<<max_unknown_count<<",\"first_max_unknown\":"<<first_unknown<<"}\n";
}catch(const exception& e){cerr<<e.what()<<'\n';return 1;}}
