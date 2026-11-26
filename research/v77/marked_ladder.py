"""Khattar–Gidney 2025, Theorem 5.1, independently implemented."""
def marked_steps(n):
    if n < 2: raise ValueError('n >= 2 required')
    marked = [True] + [False] * n
    steps = []
    while marked.count(False) > 2:
        for t in range(n, -1, -1):
            free = [i for i in range(t + 1, n + 1) if not marked[i]]
            if marked[t] and len(free) >= 2:
                x, y = free[:2]
                marked[t], marked[x], marked[y] = False, True, True
                steps.append((t, x, y))
                break
        else: raise AssertionError('no legal move')
    return steps, tuple(i for i in range(n + 1) if not marked[i])

def run_tests():
    count = 0
    for n in range(2, 13):
        steps, (a,b) = marked_steps(n)
        assert len(steps) == n-2
        for z in range(1 << n):
            src = [0] + [(z>>i)&1 for i in range(n)]
            q = src[:]
            for t,x,y in steps:
                q[t] ^= q[x]&q[y]
                if t: q[t] ^= 1
            assert (q[a]&q[b]) == int(z == (1<<n)-1)
            for t,x,y in reversed(steps):
                if t: q[t] ^= 1
                q[t] ^= q[x]&q[y]
            assert q == src
            count += 1
    print('marked ladder exhaustive inputs:',count)
if __name__ == '__main__': run_tests()
