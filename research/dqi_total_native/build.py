"""Reproduce the raw-syndrome complete KMB using pinned upstream native writer and GF12 tensor."""
import ast
from pathlib import Path
src=Path("emit_opt.cpp").read_text().split("W w;")[0]
src=src.replace("#include <bits/stdc++.h>","#include <algorithm>\n#include <array>\n#include <cassert>\n#include <cstdint>\n#include <fstream>\n#include <iostream>\n#include <map>\n#include <numeric>\n#include <set>\n#include <string>\n#include <vector>\n#include <utility>")
src=src.replace("Q=851","Q=900").replace('reg("P"+to_string(i)','reg("S"+to_string(i)').replace('reg("V"+to_string(i)','reg("S"+to_string(35+i)')
codes=next(ast.literal_eval(n.value) for n in ast.parse(Path("crt882.py").read_text()).body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="CODES" for x in n.targets))
assert len(codes)==510 and sum(x>=4096 for x in codes)==42
tail=Path("total.cpp.in").read_text().replace("__CODES__",",".join(map(str,codes)))
Path("total.cpp").write_text(src+tail)
