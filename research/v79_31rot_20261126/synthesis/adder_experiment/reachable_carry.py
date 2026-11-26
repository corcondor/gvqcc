"""Exact reachable-range pruning of the split21-bit Horner carry chart.
P=odd(address)*T,0<=T<=4095. Only address0 can cross2^16-Klo;
its constant-high word is even, so its carry changes only highbit0.
"""
import split_carry as A
import clean_lookup as L
from pathlib import Path
import json

ACTIVE=[];CERT=[]
for a,k in enumerate(A.H.CONSTANT):
 k=int(k);low=k&65535;maximum=int(A.H.ODD[a])*4095
 assert 0<=maximum<65536
 possible=bool(low and maximum>=65536-low)
 if possible:ACTIVE.append(a)
 CERT.append({'address':a,'constant':k,'odd_multiplier':int(A.H.ODD[a]),'T_max':4095,'product_min':0,'product_max':maximum,'K_low':low,'carry_threshold':65536-low,'carry_possible':possible,'K_high':k>>16,'carry_high_xor':((k>>16)^((k>>16)+1))&31})
assert ACTIVE==[0]
assert all(CERT[a]['carry_high_xor']==1 for a in ACTIVE)


def carry(b):
 old=0
 for a in ACTIVE:
  mask=1<<a;L.flag(b,old^mask,A.HIGH[1:]);old=mask
  A.compare_constant(b,int(A.H.CONSTANT[a])&65535,A.HIGH[0],A.FLAG,A.HIGH[1:])
 L.flag(b,old,A.HIGH[1:])


def high(b,negative=False):
 hi=[int(k)>>16 for k in A.H.CONSTANT]
 events=[]
 for j in range(5):
  mask=sum(1<<a for a,k in enumerate(hi)if k>>j&1)
  if mask:events.append((mask,A.Op(33,(A.FLAG,A.HIGH[j]))))
 if negative:events.reverse()
 old=0
 for mask,op in events:
  b.add(*A.H.flag_ops(old^mask),op);old=mask
 b.add(*A.H.flag_ops(old))

if __name__=='__main__':
 A.add_low=L.add_low;A.carry=carry;A.high_extension=high
 A.main('_reachable')
 (A.HERE/'reachable_carry_integer_certificate.json').write_text(json.dumps({'statement':'P=odd*T with0<=T<=4095;carrypossibleiff product_max>=65536-K_low;onlyaddress0 active anditsK_high even','rows':CERT,'active_addresses':ACTIVE},indent=2))
