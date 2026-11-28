"""Emit exact native #246 variant; expected input already in D,H frame."""
import sys
from pathlib import Path
s=Path('half_magnitude.cpp').read_text()
inc=Path('quotient_spectral.cpp.inc').read_text()
i=s.index('void magnitude(){')
s=s[:i]+inc+s[i:]
base='for(int i=0;i<17;i++)for(int k=1;k<=17-i;k++)mx(aa(17-i),bb(17-k),aa(17-i-k));'
back='for(int i=16;i>=0;i--)for(int k=17-i;k>=1;k--)mx(aa(17-i),bb(17-k),aa(17-i-k));'
assert s.count(base)==s.count(back)==1
s=s.replace(base,'Words a0,b0;for(int i=0;i<18;i++)a0.push_back(aa(17-i));for(int i=1;i<18;i++)b0.push_back(bb(17-i));quotient(a0,b0,false);').replace(back,'quotient(a0,b0,true);')
if len(sys.argv)>1 and sys.argv[1] in ('all','tri','transport'):
 s=s.replace('conv17(q,T,U);','spectral_conv17(q,T,U);').replace('conv17(q,U,V0);','spectral_conv17(q,U,V0);')
if len(sys.argv)>1 and sys.argv[1] in ('tri','transport'):
 orig='for(int j=0;j<17;j++)for(int i=0;2*i<=j;i++)mx(q[i],h(j+1),h(j-2*i));'
 assert s.count(orig)==1
 s=s.replace(orig,'odd_plan();Words hrev;for(int i=17;i>=0;i--)hrev.push_back(h(i));sparse_triangle(hrev,q);')
if len(sys.argv)>1 and sys.argv[1]=='transport':
    p='void rank_update'
    s=s.replace(p,'void rank_run(const Words&,const Words&,const Words&,const vector<pair<int,vector<int>>>&);\n'+p,1)
    s=s.replace('for(int i=0;i<L;i++){','vector<pair<int,vector<int>>> terms;for(int i=0;i<L;i++){',1)
    s=s.replace('rank_update(a,d,t,x,v);\n  }','terms.emplace_back(x,v);\n  }rank_run(a,d,t,terms);',1)
    s=s.replace('for(int x=0;x<33;x++){','vector<pair<int,vector<int>>> terms;for(int x=0;x<33;x++){',1)
    s=s.replace('rank_update(a,b,t,x,v);\n }','terms.emplace_back(x,v);\n }rank_run(a,b,t,terms);',1)
    s=s.replace('}else for(int i=0;i<L;i++){','}else {vector<pair<int,vector<int>>> terms;for(int i=0;i<L;i++){',1)
    s=s.replace('rank_update(a,b,t,x,v);\n }','terms.emplace_back(x,v);\n }rank_run(a,b,t,terms);}',1)
Path('half_spectral.cpp').write_text(s)
