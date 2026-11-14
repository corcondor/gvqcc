"""Finite exact cost screen for selected rational/elliptic/genus-two recipes.

Only ordinary places with explicit binary kernels of degrees 1,2,3,4,6
are priced. This is not a lower bound for arbitrary Chudnovsky algorithms,
derivative kernels, or for unrestricted GF24 multiplication.
"""
import json
import math
from pathlib import Path

from inverse_v2_optimize import tensor, mul

COST = {n: len(tensor(n)) for n in (1, 2, 3, 4, 6)}


def allocate(required, places, costs):
    # Coordinates above required are allowed, so an extra place is never
    # accidentally ruled out merely because its degree overshoots.
    dp = {0: (0, {})}
    for degree in sorted(places):
        for _ in range(min(places[degree], math.ceil(required / degree))):
            old = dict(dp)
            for reached, (cost, use) in old.items():
                nxt = min(required, reached + degree)
                proposal = cost + costs[degree]
                if proposal < dp.get(nxt, (10**9, {}))[0]:
                    u = dict(use)
                    u[degree] = u.get(degree, 0) + 1
                    dp[nxt] = proposal, u
    return dp.get(required)


def mobius(n):
    primes, p = 0, 2
    while p * p <= n:
        if n % p == 0:
            n //= p
            primes += 1
            if n % p == 0:
                return 0
            while n % p == 0:
                n //= p
        p += 1
    if n > 1:
        primes += 1
    return -1 if primes % 2 else 1


def p1_count(q, degree):
    if degree == 1:
        return q + 1
    return sum(mobius(d) * q**(degree // d) for d in range(1, degree + 1)
               if degree % d == 0) // degree


def elliptic_places(q, trace, degrees):
    s = [2, trace]
    for n in range(2, max(degrees) + 1):
        s.append(trace * s[-1] - q * s[-2])
    points = {n: q**n + 1 - s[n] for n in range(1, max(degrees) + 1)}
    return {d: sum(mobius(e) * points[d // e] for e in range(1, d + 1)
                   if d % e == 0) // d for d in degrees}


def main():
    checks = 0
    for n in COST:
        for i in range(n):
            for j in range(n):
                value = 0
                for a, b, c in tensor(n):
                    if a >> i & 1 and b >> j & 1:
                        value ^= c
                assert value == mul(1 << i, 1 << j, n)
                checks += 1
    p1, elliptic = [], []
    for m in (1, 2, 3, 4, 6):
        q, n = 1 << m, 24 // m
        degrees = [d for d in range(1, 7) if m * d in COST]
        costs = {d: COST[m * d] for d in degrees}
        places = {d: p1_count(q, d) for d in degrees}
        result = allocate(2 * n - 1, places, costs)
        p1.append(dict(base_field=q, relative_degree=n, required_coordinates=2*n-1,
                       place_counts=places, binary_place_costs=costs,
                       cheapest_catalogue_cost=result[0], selected_places=result[1]))
        options = []
        for trace in range(-math.isqrt(4 * q), math.isqrt(4 * q) + 1):
            available = elliptic_places(q, trace, degrees)
            if min(available.values()) < 0:
                continue
            result = allocate(2 * n, available, costs)
            if result:
                options.append(dict(trace=trace, place_counts=available,
                                    cost=result[0], selected_places=result[1]))
        best = min(options, key=lambda x: x['cost'])
        elliptic.append(dict(base_field=q, relative_degree=n, required_coordinates=2*n,
                             optimistic_best=best, note='All Hasse-interval integer traces admitted; existence/injectivity not asserted.'))
    genus2 = []
    q = 4
    for a1 in range(-5, 6):
        for a2 in range(-8, 25):
            disc = a1*a1 - 4*(a2 - 2*q)
            if disc < 0:
                continue
            roots = [(-a1 + sign*math.sqrt(disc))/2 for sign in (-1, 1)]
            if any(abs(x) > 4 + 1e-12 for x in roots):
                continue
            n1 = q+1+a1
            n2 = q*q+1 - (a1*a1 - 2*a2)
            n3 = q**3+1 - (-a1**3 + 3*a1*a2 - 3*q*a1)
            if not 0 <= n1 <= 10 or (n2-n1) % 2 or (n3-n1) % 3:
                continue
            places = {1:n1, 2:(n2-n1)//2, 3:(n3-n1)//3}
            if min(places.values()) < 0:
                continue
            result = allocate(25, places, {1:3, 2:9, 3:15})
            if result:
                genus2.append(dict(a1=a1, a2=a2, place_counts=places,
                                   cost=result[0], selected_places=result[1]))
    best = min(genus2, key=lambda x: x['cost'])
    report = dict(status='BOUNDED_CONSTRUCTION_COST_SCREEN_COMPLETE',
                  explicit_binary_kernel_costs=COST, exact_kernel_basis_pairs=checks,
                  rational_line=p1, elliptic=elliptic,
                  genus2_F4_optimistic_best=best, genus2_Weil_polynomials_examined=len(genus2),
                  genus2_F4_rational_point_cap=10,
                  genus2_cap_reason='Genus-two hyperelliptic map has degree two to P1 over the finite field; 2*(4+1)=10.',
                  excluded=['higher-degree place kernels outside the explicit catalogue',
                            'derivative evaluations', 'higher genus', 'unrestricted tensor decompositions'],
                  warning='Minimum within this priced catalogue only. Field counts do not prove evaluation injectivity or construct a curve.')
    path=Path(__file__).with_suffix('.json')
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
