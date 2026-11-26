# A relation tying TWO partial columns: z_y1 + z_y2 = sum of full-column z over S.  Only the x values cared by both
# need care equations on S; the others are absorbed by the free values of y1 or y2.  Report the freedom.
# usage: pairrel.py k
import sys
from common import *
from frame import *
from gf2 import solve_linear, Ech

k = int(sys.argv[1])
F = Frame(k)
full = F.full
partial = [y for y in range(F.ny) if len(F.carex[y]) < F.nx]
from collections import Counter
print('columns', F.ny, 'full', len(full), 'partial by care count', sorted(Counter(len(F.carex[y]) for y in partial).items()))
five = [y for y in range(F.ny) if len(F.carex[y]) == 5]
for y in five:
    print(f'  five-care column {y}: cared x {F.carex[y]}')
lin = [np.ones(F.ny, np.uint8)] + [F.ybits[t] for t in range(len(F.Y))] + list(F.tagf)


def system(ys, xs):
    """care equations (over the full columns) for x in xs, summed over the partial columns ys, plus linear ones."""
    eqs, rhs = [], []
    for o in range(30):
        for x in xs:
            r = 0
            for t, y in enumerate(full):
                if F.N[o, x - 1, y]:
                    r |= 1 << t
            eqs.append(r)
            rhs.append(sum(int(F.N[o, x - 1, y]) for y in ys) & 1)
    for f in lin:
        r = 0
        for t, y in enumerate(full):
            if f[y]:
                r |= 1 << t
        eqs.append(r)
        rhs.append(sum(int(f[y]) for y in ys) & 1)
    return eqs, rhs


for i in range(len(five)):
    for j in range(i + 1, len(five)):
        y1, y2 = five[i], five[j]
        both = [x for x in F.carex[y1] if x and x in F.carex[y2]]
        either = sorted(set(F.carex[y1]) | set(F.carex[y2]))
        sol = solve_linear(*system([y1, y2], both), len(full))
        print(f'pair ({y1},{y2}): cared by both {both}, by either {either}: ' +
              (f'support solution space dim {len(sol[1])}' if sol else 'NO solution'))
for y in five:
    sol = solve_linear(*system([y], [x for x in F.carex[y] if x]), len(full))
    print(f'single {y}: ' + (f'support solution space dim {len(sol[1])}' if sol else 'NO solution'))
