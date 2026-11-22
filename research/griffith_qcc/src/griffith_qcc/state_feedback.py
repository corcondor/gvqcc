"""Phase-exact reversible state-register / conditional-update identities.

No clean ancilla required. Each identity operates on arbitrary dirty targets
and is exact on every basis state, hence on every superposition.
These are small components, not an independently scored GVQCC circuit.
Sources for context: Cuccaro quant-ph/0410184, Google Qualtran (Apache-2.0),
ETH Reqomp (MIT). Implementations and identities below are independently written.
"""


def t_flip(control: int, data: int, target: int):
    """Target ^= control & data. All qubits arbitrary, preserved except target."""
    assert len({control, data, target}) == 3
    return [("CCX", control, data, target)]


def d_latch(control: int, old: int, new: int):
    """Reversible data latch: conditional swap retains the old value."""
    assert len({control, old, new}) == 3
    return [("CSWAP", control, old, new)]


def d_latch_via_ccx(control: int, old: int, new: int):
    assert len({control, old, new}) == 3
    return [("CX", old, new), ("CCX", control, new, old), ("CX", old, new)]


def mux_naive(select: int, a: int, b: int, target: int):
    """target ^= (b if select else a), leaving a,b,select unchanged."""
    assert len({select, a, b, target}) == 4
    return [("X", select), ("CCX", select, a, target),
            ("X", select), ("CCX", select, b, target)]


def mux_factored(select: int, a: int, b: int, target: int):
    """Same XOR-oracle with 1 CCX instead of 2, no ancilla."""
    assert len({select, a, b, target}) == 4
    return [("CX", a, target), ("CX", a, b),
            ("CCX", select, b, target), ("CX", a, b)]


def parity_control_naive(enable: int, inputs, target: int):
    """target ^= enable & XOR(inputs) via one CCX per input."""
    inputs = list(inputs)
    assert inputs and len(set([enable, target] + inputs)) == len(inputs)+2
    return [("CCX", enable, inp, target) for inp in inputs]


def parity_control_factored(enable: int, inputs, target: int):
    """Same XOR-oracle with one CCX, 2*(m-1) CX and zero ancillas."""
    inputs = list(inputs)
    assert inputs and len(set([enable, target] + inputs)) == len(inputs)+2
    pivot = inputs[0]
    before = [("CX", src, pivot) for src in inputs[1:]]
    return before + [("CCX", enable, pivot, target)] + list(reversed(before))


def lfsr_step(register):
    """Invertible linear feedback: (a,b,c,d)->(b,c,d,a XOR d)."""
    q = list(register)
    assert len(q)>=2 and len(set(q))==len(q)
    return [("CX", q[-1], q[0])] + [("SWAP", q[i], q[i+1])
                                      for i in range(len(q)-1)]
