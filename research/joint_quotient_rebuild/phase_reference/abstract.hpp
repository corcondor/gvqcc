#pragma once
#include <bitset>
// Same conservative linear/product-atom abstraction as the previously committed
// zero_scan.cpp / recover_scan.cpp; retain active classical guard SSA symbols.
constexpr int MAX=2048;using V=bitset<MAX>;
struct Key{V a,b;bool operator==(const Key&o)const{return a==o.a&&b==o.b;}};
struct H{size_t operator()(const Key&k)const{return hash<V>()(k.a)^rotl(hash<V>()(k.b),1);}};
struct Abstract{
 vector<V> q,st;V one;int n=1;unordered_map<Key,int,H>prod;unordered_map<I,V> bits;U rebases=0;
 Abstract(int Q):q(Q),st(1){one[0]=1;st[0]=one;}
 void rebase(){vector<V> rows(n),co(n);rows[0]=one;co[0]=one;int r=1;auto transform=[&](V&x){V z=x,t;for(size_t p=z._Find_first();p<MAX;p=z._Find_first()){if(rows[p].any()){z^=rows[p];t^=co[p];}else{rows[p]=z;co[p].set(r++);t^=co[p];break;}}x=t;};for(auto&x:q)transform(x);for(auto&x:st)transform(x);n=r;prod.clear();bits.clear();rebases++;}
 V fresh(){assert(n<MAX);V v;v.set(n++);return v;}
 V bit(I b,int known){if(known<2)return known?one:V{};auto it=bits.find(b);if(it!=bits.end())return it->second;return bits.emplace(b,fresh()).first->second;}
 void invalidate(I b){bits.erase(b);}
 V andp(V a,V b){if(a.none()||b.none())return {};if(a==one)return b;if(b==one)return a;if(a==b)return a;if((a^b)==one)return {};bool ac=a[0],bc=b[0];a[0]=b[0]=0;V ret;if(ac)ret^=b;if(bc)ret^=a;if(ac&&bc)ret^=one;if(a==b)return ret^a;size_t ha=hash<V>()(a),hb=hash<V>()(b);if(ha>hb||(ha==hb&&a.to_string()>b.to_string()))swap(a,b);auto [it,add]=prod.emplace(Key{a,b},n);if(add)n++;assert(n<MAX);ret.flip(it->second);return ret;}
 int known(const V&v){return v.none()?0:v==one?1:2;}
};
