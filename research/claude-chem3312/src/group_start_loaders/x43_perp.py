# export Theta-perp of loader k (210-bit vectors as 4 x 64-bit words) for the C++ design search
import sys
from planner import *
k = int(sys.argv[1])
S = Space(Frame(k))
M = (1 << 64) - 1
print(len(S.perp))
for p in S.perp:
    print(p & M, (p >> 64) & M, (p >> 128) & M, (p >> 192) & M)
