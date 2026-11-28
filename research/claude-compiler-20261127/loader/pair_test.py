import sys, pickle
from frame import *
from gf2 import Ech
from solve import check_function, needed_rows
from solve3 import solve_pair

k = int(sys.argv[1]); cov = pickle.load(open(sys.argv[2], 'rb'))
forced = pickle.load(open(sys.argv[2].replace('.pkl', '.five.pkl'), 'rb'))
F = Frame(k)
five = [y for y in range(F.ny) if len(F.carex[y]) == 5]
pair = [y for y in five if y not in forced]
sol = solve_pair(F, cov, 13, pair[:2], forced=forced)
bad, lx = check_function(F, cov, sol)
rows, hrows, lin = needed_rows(F, sol)
H = Ech(rows + hrows + lin).n
print(f'function mismatches {bad}; relations {sol["nrel"]}; rank of needed high functions {H}; predicted Toffolis {len(cov) + H - 10}; free columns {sol["free"]}')
pickle.dump(sol, open(f'sol_pair_k{k}.pkl', 'wb'))
