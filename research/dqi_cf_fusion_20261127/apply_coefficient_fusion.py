"""Strict AST splice: preserve every route, including the owner's CF repair.
Only use after checking immediate phase repayment and disjoint/restored mul operands.
This is not a verified full converter replacement.
"""
import ast, argparse, pathlib, textwrap, hashlib
LOW_OLD = """
ar.mul_xor0(b, q1, e1, X)
B, own = P.get_B(b, L, q1)
h, lBn = _bnf(b, B, F)
for j in range(12):
    b.ccx(h, e1[j], X[j])
_bnf_erase(b, h, lBn)
"""
LOW_NEW = """
B, own = P.get_B(b, L, q1)
h, lBn = _bnf(b, B, F)
assert len(set(map(str, list(q1) + list(e1) + list(X) + [h]))) == 37
assert str(B) not in set(map(str, q1))
b.cx(h, q1[0])
ar.mul_xor0(b, q1, e1, X)
b.cx(h, q1[0])
_bnf_erase(b, h, lBn)
"""
CG_BUILD_OLD = """
ar.mul_xor0(b, q1, g[-2], CG)
B, own = P.get_B(b, L, q1)
h, lBn = _bnf(b, B, F)
for j in range(12):
    b.ccx(h, g[-2][j], CG[j])
"""
CG_BUILD_NEW = """
B, own = P.get_B(b, L, q1)
h, lBn = _bnf(b, B, F)
assert len(set(map(str, list(q1) + list(g[-2]) + list(CG) + [h]))) == 37
assert str(B) not in set(map(str, q1))
b.cx(h, q1[0])
ar.mul_xor0(b, q1, g[-2], CG)
b.cx(h, q1[0])
"""
CG_ERASE_OLD = """
for j in range(12):
    b.ccx(h, g[-2][j], CG[j])
_bnf_erase(b, h, lBn)
if own:
    P.clear_zero_flag(b, q1, B)
ar.erase_product(b, q1, g[-2], CG)
"""
CG_ERASE_NEW = """
b.cx(h, q1[0])
ar.erase_product(b, q1, g[-2], CG)
b.cx(h, q1[0])
_bnf_erase(b, h, lBn)
if own:
    P.clear_zero_flag(b, q1, B)
"""
def _stmts(src):
    return [ast.dump(x, include_attributes=False) for x in ast.parse(src).body]
def _find(fn, old):
    a = [ast.dump(x, include_attributes=False) for x in fn.body]
    b = _stmts(old)
    hits = [i for i in range(len(a)-len(b)+1) if a[i:i+len(b)] == b]
    if len(hits) != 1:
        raise ValueError(f'{fn.name}: expected exactly one matched block, found {len(hits)}')
    i = hits[0]
    return fn.body[i].lineno-1, fn.body[i+len(b)-1].end_lineno
def rewrite(source):
    before = ast.parse(source)
    fs = {x.name: x for x in before.body if isinstance(x, ast.FunctionDef)}
    ranges = []
    for name, old, new in [('lower_payload', LOW_OLD, LOW_NEW),
                           ('cg_part', CG_BUILD_OLD, CG_BUILD_NEW),
                           ('cg_part', CG_ERASE_OLD, CG_ERASE_NEW)]:
        if name not in fs:
            raise ValueError(f'no {name}')
        a, b = _find(fs[name], old)
        ranges.append((a, b, textwrap.indent(new.strip(), '    ')+'\n'))
    lines = source.splitlines(keepends=True)
    for a, b, new in sorted(ranges, reverse=True):
        lines[a:b] = [new]
    output = ''.join(lines)
    after = ast.parse(output)
    def rest(t):
        return [ast.dump(x, include_attributes=False) for x in t.body
                if not (isinstance(x, ast.FunctionDef) and x.name in ('lower_payload', 'cg_part'))]
    assert rest(before) == rest(after)
    compile(output, '<transformed>', 'exec')
    return output
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=pathlib.Path)
    p.add_argument('output', type=pathlib.Path)
    args = p.parse_args()
    if args.source.resolve() == args.output.resolve() or args.output.exists():
        raise SystemExit('refuse in-place rewrite or overwrite')
    result = rewrite(args.source.read_text())
    args.output.write_text(result)
    print('input_sha256', hashlib.sha256(args.source.read_bytes()).hexdigest())
    print('output_sha256', hashlib.sha256(args.output.read_bytes()).hexdigest())
    print('3 matched AST blocks; all other top-level statements preserved; Python compile PASS')
if __name__ == '__main__':
    main()
