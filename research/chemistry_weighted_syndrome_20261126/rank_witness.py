"""Standalone exact checks for protected-row obstruction and DP recurrence."""
from itertools import product
from math import inf
def check_rank5(columns):
    return all(any((mask & v).bit_count() % 2 for v in columns) for mask in range(1, 32))
def min_weight_syndrome(signatures, costs, n):
    dp = [inf] * (1 << n)
    dp[0] = 0
    for s, w in zip(signatures, costs):
        dp = [min(dp[t], dp[t ^ s] + w) for t in range(1 << n)]
    return dp
if __name__ == '__main__':
    assert check_rank5([1,22,26,16,21])
    assert check_rank5([22,14,25,11,21])
    import random
    rng = random.Random(6310)
    for _ in range(200):
        sig = [rng.randrange(1,32) for _ in range(8)]
        costs = [rng.randrange(1,30) for _ in sig]
        dp = min_weight_syndrome(sig,costs,5)
        brute = [inf]*32
        for bits in product((0,1),repeat=len(sig)):
            t=0; c=0
            for b,s,w in zip(bits,sig,costs):
                if b: t^=s; c+=w
            brute[t]=min(brute[t],c)
        assert dp == brute
    print('PASS: two rank-5 witnesses, 200 exact syndrome-DP vs exhaustive subset checks')
