# V79 resident-frame and quotient-space synthesis experiments

## Authoritative donor

`GVQCC_V79_Width23to36_WholeCircuit_RESEARCH_ONLY.zip`, SHA256 `a1439ab581e4f6140577f293b47678eacb5427e456ec3fa63217a8cf5d4d157a`.

The donor candidate is `runs/tree36.kmb`, SHA256 `e81cbe79c7b6ac2aef27ff5539d458ff2726e3b0c9bb01f26e17fdcae4cd347c`, not `runs/q36.kmb` (the latter is a 2,151-CCX matched control).

## Completed whole native circuits

| Circuit | Q | CCX | Instructions | Generic rotations | Independent formula cost |
|---|---:|---:|---:|---:|---:|
| V79 tree36 | 36 | 1,267 | 53,942 | 7,747 | 2,298,148.0759806475 |
| persistent36 | 36 | 1,267 | 50,945 | 7,747 | 2,298,148.0759806475 |
| joint36_s0 | 36 | 1,244 | 50,754 | 7,747 | 2,297,320.0759806475 |
| quotient36 | 36 | 1,234 | 51,423 | 7,747 | 2,296,960.0759806475 |
| exchange36 | 36 | 1,230 | 51,582 | 7,747 | 2,296,816.0759806475 |

All four new circuits pass independent replay of every 2^22 input, exact symbolic HMR correction checks, 128-bit modular phase comparison with the original plan, complete input/workspace restoration, and the exact tolerance test on all 3,133,452 legal inputs. The residual phase margin is unchanged: 138,112,178. Receipt JSON files contain the circuit SHA256 and verification counts. This helper is not the official KickMix verifier; any official run is a separate root-agent experiment.

## Three changes, with their algebraic grounds

1. **Persistent resident frame.** Each stored wire is `q_i=f*ell_i(x)` for an independent set of linear forms over GF(2). A requested flag `q_v=XOR_i c_i q_i` is materialized in any pivot with c_p=1. Replacing ell_p by v is invertible, so there is no need to immediately undo the CNOT chain. The next request is evaluated in the updated basis. Before HMR, each actual stored form is reconstructed from the current input bits, so the phase correction is exact.

2. **Joint first-factor orientation and space scheduling.** For a rank-two signed predicate, its three nonzero constraint directions describe the same affine plane. Their signs and representatives are transformed exactly. The compiler searches which direction is first and which resident subspaces hold these first factors. Each proposed representation retains the exact original coset expansion. The actual paid count and physical capacity guide the prefix-tree dynamic program.

3. **Quotient hubs from pair differences.** The original requested-mask dictionary is insufficient to describe every useful retained space. Choose a subspace U spanned by pairwise differences of requested masks. Retain conditional products for a basis of U. Every nonzero quotient class v+U then needs only one additional conditional product, and all requests in that class follow by CNOT combinations. With c=dim(U) and k nonzero quotient classes, the compute count is c+k, using at most c+1 carrier wires (plus the prefix/second-guard allocator). The candidate generator checks actual matrix ranks and exact symbolic maps; no Taylor or higher-order residual is dropped.

Original V79 chosen prefixes use 674 first-factor products although the corresponding total full-span rank is 586 (578 from compulsory rank-one constraints). The difference is a width and schedule cost, not a universal lower bound. The quotient-space search targets this overhead. A quadratic-vector-space audit finds only three dependencies among 457 rank-two predicates, so simply assuming very low tensor rank would be unjustified.

## Reproduction

Run inside this directory. `donor/` contains the unchanged recovered Python modules; the three symlinks point to the pinned recovered V79 phase plan, header, and donor frequency selection.

```sh
python search_tree.py 36 persistent36 0 2 1 1 0
python search_tree.py 36 joint36_s0 0 7 2 1 0
python search_tree.py 36 quotient36 0 7 2 1 1
python run_exchange.py exchange36
g++ -O3 -std=c++17 phasecheck.cpp -o phasecheck
PYTHONPATH=donor python donor/verify_echo.py quotient36 recip.plan.json
PYTHONPATH=donor python donor/cost.py quotient36
```

`search_tree.py` exposes `SearchTree(Q,scale,S,policy,seed,penalty,policies,tries,persistent,hubs)` for integration with other phase-emission policies. Nonempty S uses the inherited hybrid direct/toggle emitter; this is a separate cost tradeoff and must be tested as a full new circuit.

## Follow-up neighborhood

`quotient_exchange.py` additionally counts the zero quotient exactly and optimizes U by one-dimensional subspace exchanges. Remove one retained direction, then insert the pair difference that minimizes the exact quotient-class count. Only strict class-count improvements are accepted. `run_exchange.py` combines this new neighborhood with the same complete circuit emitter. This is a change of retained subspace, not a repetition of random seeds.

The exchange variant is now complete and independently verified. Compared with V79, first-factor products fall from 674 to 643 (31 saved), second-factor products remain 456, and prefix/other CCX fall from 137 to 131 (6 saved). The final total is 1,230 CCX. The kernel search evaluates 637 distinct retained spaces and accepts one-dimensional changes saving 47 quotient classes across all examined capacity cases; only four additional CCX savings survive the whole-circuit allocator compared with quotient36. This distinction prevents treating every local gain as additive.
