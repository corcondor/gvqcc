# Branch-aware Boolean algebra screen for DQI e4

The exact e4 source member has SHA-256
\`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355\`.
All 840 input qubits are unconstrained initial variables. Scratch and
classical registers start at zero. X-basis outcomes are independent symbols.
No native replacement circuit was emitted and the DQI score is unchanged.

The scanner propagates sparse Boolean algebraic normal form. Multiplication
expands the full distributive product within the configured limits, with
idempotence of repeated variables and cancellation of duplicated monomials.
PUSH/POP regions are evaluated with a symbolic Boolean selector at their
join. A derived expression beyond the degree or monomial limits becomes a
fresh unconstrained variable. Equality that survives this overapproximation
is exact for the original Boolean values. Clifford sign operations do not
change the Boolean state, so tests for simplifying CCZ independently compare
their sign exponents. Pairwise complement equality is checked by an exact
sparse-form comparison within hash buckets.

| Quantity | Result |
|---|---:|
| Gates scanned | 58,868,734 |
| CCX, CCZ, CSWAP checked | 363,654 / 7,000 / 12,240 |
| Direct phase/value simplifications | 0 |
| Positions with 889 nonconstant forms distinct modulo complements, at degree 12 and 16 monomials | 9,324,913 |

The rank probes cover the entrance and midpoint of every peak span in the
existing reset-separated lifetime graph. The ranks are of the abstract
polynomials modulo constants. Full abstract rank does not show actual
independence of the wires because overflow may erase a relation. The
analysis excludes neither other polynomial rewrites nor a new
arithmetic architecture. It specifically found no ready simplification
or full-width improvement in this bounded model.

\`\`\`sh
g++ -O3 -std=c++17 -DMAX_TERMS=16 -DMAX_DEGREE=12 anf_width.cpp -o /tmp/dqi-anf
python test_anf.py /tmp/dqi-anf
python peak_probes.py "$DQI_E4_INTERVALS" /tmp/dqi-probes.txt
/tmp/dqi-anf "$DQI_E4_KMB" /tmp/dqi-hits.tsv /tmp/dqi-probes.txt /tmp/dqi-ranks.tsv
\`\`\`
