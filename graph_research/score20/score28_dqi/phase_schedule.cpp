// Conservative zero-lifetime shortening by commuting births/scrubs.
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
static void measure(const vector<Life>& lives, bool changed, const char* label, uint64_t n) {
    map<uint64_t,int> events;
    for(const Life& l:lives){
        uint64_t start=changed?l.new_first:l.first, stop=changed?l.new_stop:l.stop;
        if(start>stop)throw runtime_error("crossed");
        events[start]++;events[stop]--;
    }
    int live=0, peak=0;
    uint64_t span=0, ranges=0, first=0;
    bool previous_at_peak=false;
    for(auto i=events.begin();i!=events.end();i++){
        live+=i->second;
        auto next=std::next(i);
        if(next==events.end())break;
        auto width=min(n,next->first)-i->first;
        if(!width)continue;
        if(live>peak){
            peak=live;span=0;ranges=0;first=i->first;previous_at_peak=false;
        }
        if(live==peak){span+=width;ranges+=!previous_at_peak;}
        previous_at_peak=live==peak;
    }
    cout<<"\""<<label<<"\":{\"peak\":"<<peak<<",\"peak_spans\":"<<ranges<<",\"peak_positions\":"<<span<<",\"first_peak\":"<<first<<"}";
}
int main(int argc,char**argv) {try{
    if(argc!=4)throw runtime_error("usage KMB intervals.tsv output.tsv");
    Tape tape(argv[1]);
    ifstream table(argv[2]);
    string line;
    getline(table,line);
    vector<Life> lives;
    unsigned q,abi;
    uint64_t start,last;
    while(table>>q>>start>>last>>abi){
        if(q>=tape.nq||last>tape.n)throw runtime_error("bad interval");
        lives.push_back({q,start,last+1,start,last+1,bool(abi)});
    }
    vector<size_t> by_first,by_end;
    for(size_t i=0;i<lives.size();i++)if(!lives[i].abi){
        by_first.push_back(i);by_end.push_back(i);
    }
    sort(by_first.begin(),by_first.end(),[&](size_t i,size_t j){return lives[i].first<lives[j].first;});
    sort(by_end.begin(),by_end.end(),[&](size_t i,size_t j){return lives[i].stop<lives[j].stop;});
    size_t si=0,ei=0;
    vector<int64_t> last_q(tape.nq,-1), last_c(tape.nb,-1);
    vector<vector<size_t>> pending_target(tape.nq),pending_read(tape.nq);
    vector<bool> active(lives.size());
    vector<size_t> pending_global;
    auto finish=[&](size_t id,uint64_t now){
        if(!active[id])return;
        active[id]=false;
        lives[id].new_first=now;
    };
    auto finish_list=[&](vector<size_t>& list,uint64_t now){
        for(size_t id:list)finish(id,now);
        list.clear();
    };
    int64_t last_scope=-1;
    unsigned depth=0;
    for(uint64_t pos=0;pos<tape.n;pos++){
        Op op=tape.step();
        if(op.code==0x81||op.code==0x01){
            finish_list(pending_global,pos);
            last_scope=pos;
            if(op.code==0x81)depth++;
            else{if(!depth)throw runtime_error("stack");depth--;}
        }
        for(unsigned j=0;j<op.count;j++)finish_list(pending_target[op.qubits[j]],pos);
        unsigned writes=0;
        if(op.base==0x11||op.base==0x12||op.base==0x50||op.base==0x21||op.base==0x31)writes=1;
        if(op.base==0x22||op.base==0x32)writes=2;
        for(unsigned j=op.count-writes;j<op.count;j++)finish_list(pending_read[op.qubits[j]],pos);
        while(ei<by_end.size()&&lives[by_end[ei]].stop==pos+1){
            Life& life=lives[by_end[ei++]];
            if(depth||op.cond>=0||(op.base!=0x12&&op.base!=0x50)||op.qubits[0]!=life.q)throw runtime_error("unexpected interval terminator");
            int64_t anchor=max({int64_t(life.first),last_q[life.q],last_scope});
            if(op.bit>=0)anchor=max(anchor,last_c[op.bit]);
            // Physical wire is live during the relocated R/HMR itself.
            life.new_stop=min(pos+1,uint64_t(anchor+2));
        }
        while(si<by_first.size()&&lives[by_first[si]].first==pos){
            size_t id=by_first[si++];
            auto q=lives[id].q;
            if(depth||op.cond>=0||op.count==0)continue;
            if(op.base!=0x11&&op.base!=0x21&&op.base!=0x31)continue;
            if(op.qubits[op.count-1]!=q)continue;
            active[id]=true;
            pending_target[q].push_back(id);
            pending_global.push_back(id);
            for(unsigned j=0;j+1<op.count;j++)pending_read[op.qubits[j]].push_back(id);
        }
        for(unsigned j=0;j<op.count;j++)last_q[op.qubits[j]]=pos;
        if(op.bit>=0)last_c[op.bit]=pos;
        if(op.cond>=0)last_c[op.cond]=pos;
    }
    unsigned left=0,right=0,clamped=0;
    ofstream out(argv[3]);
    out<<"q\tfirst\tlast\tnew_first\tnew_last\tabi\n";
    for(auto& l:lives){
        if(l.new_first>=l.new_stop){l.new_first=l.first;l.new_stop=l.stop;clamped++;}
        left+=l.new_stop<l.stop;right+=l.new_first>l.first;
        out<<l.q<<'\t'<<l.first<<'\t'<<(l.stop-1)<<'\t'<<l.new_first<<'\t'<<(l.new_stop-1)<<'\t'<<l.abi<<'\n';
    }
    cout<<"{\"ops\":"<<tape.n<<",\"intervals\":"<<lives.size()<<",\"shifted_births\":"<<right<<",\"shifted_resets\":"<<left<<",\"clamped\":"<<clamped<<",";
    measure(lives,false,"original",tape.n);
    cout<<",";
    measure(lives,true,"rescheduled",tape.n);
    cout<<"}\n";
    return 0;
}catch(const exception& e){cerr<<e.what()<<"\n";return 1;}}
