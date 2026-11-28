#define main live_main
#include "live.cpp"
#undef main
int main(){
    Pass p(8,0,false,true);auto&e=p.e;
    auto a=e.fresh(),b=e.fresh(),c=e.fresh(),u=e.fresh(),v=e.fresh(),z=e.fresh(),t=e.fresh();
    auto w=e.x(e.mul(c,e.x(e.x(e.mul(a,b),u),v)),e.mul(e.neg(c),z));
    vector<F> f{a,b,c,u,v,z,t,w}; Guard g(e);
    assert(!p.span_find(e.mul(a,b),f,UINT32_MAX,false).found);
    assert(!p.span_find(e.mul(a,c),f,UINT32_MAX,false).found);
    assert(!p.span_find(e.mul(b,c),f,UINT32_MAX,false).found);
    auto r=p.observed(g,f,0,1,2,false);
    if(!r.found || r.constant || r.wires!=vector<U>{3,4,7}) return 1;
    uint64_t count=0;
    for(U m=0;m<128;m++){
        bool A=m&1,B=m&2,C=m&4,Uu=m&8,V=m&16,Z=m&32;
        bool W=(C&&(A*B^Uu^V))^(!C&&Z);
        bool before=A&&B&&C,after=(C&&Uu)^(C&&V)^(C&&W);
        assert(before==after); count+=before;
    }
    cout<<"128 truth assignments; "<<count<<" negative signs; exact engine emitted CZ(2,3), CZ(2,4), CZ(2,7)\n";
}
