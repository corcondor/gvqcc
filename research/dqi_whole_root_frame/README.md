# Complete #306 DQI signed-root frames (research only)

Exact full parent from #306 / #299 Joint: a8b5c62e24e7e44818bd46d75f8fa00a2bb9de64965c8c07912637dd58d7ebea, 900Q, 87,704,819 ops, 317,996 static paid.
- Scope-local quantum wire permutations: absorb 287,496 unconditional SWAPs, restore 105,132 at scope exit/end, 182,364 fewer instructions. Conditional SWAPs are not absorbed. Every parent layout restored inside its own scope before pop; public register layout unchanged. Intermediate 54358e3f72b7c7e8beebc652ab0ecfbb9d6a0ed23051090377c8d0b1212c2fd8.
- #293/#297/#302 measurement debt + #307 frame transport: exact full 77-op root predicate/phase/HMR/repayment recognizer. All 23 involved wires distinct; keep 12 negative controls in their flipped frame; same signed operand trace, same 10 HMR events and same bit IDs/conditions, same paid gates, all signs restored. 4024 matched leaf blocks, 77 -> 55 ops each, 88528 fewer. Full final 87,433,927 ops, 900Q, 311202 CCX / 6686 CCZ / 108 CSWAP / 317996 static paid, SHA256 88b9a17fb0e3a3e4203bc256fb5c22a065d1c1d52436c6585a00de7130d60e3e.
- Actual paired KickMix 1.0.0 full-tape replay (common seeds and inputs): 1024 distribution 0/0 errors, mean paid 316094.017578125 both; saved622 union 411/411 (407 value, 210 phase), dense144 union 70/70 (68 value,36 phase). Every final register, scratch, public-mask and raw phase difference zero. NOT a new 102400-shot run or private salt. No observed score improvement, no universal decoder repair.
- #311: reproduced 333 maximal same-guard 99-CCX regions in exact full parent. All 333 independent product direction maps have output rank24 and no internal nonlinear-control dependence in this abstraction. Transport up to 30000 later commands with strict scope/conditional/nonlinear-read barriers: blocked + remaining direction span consumes all 24 dimensions at every site. Zero direct erased-output quotient directions or individually removable terms within the tested class. Not a global impossibility theorem; #308 phase-only substitution cannot be assumed for live value-producing blocks.
- Exact CCX/CCZ commutation ledger with versioned operand hazards across the entire permutation-transformed tape: 317888 CCX/CCZ scanned; no groups of multiple equal terms eligible in this class. No new paid saving.
- 899Q one-hole clean-line allocation attempt on #306: fail closed at original command 41424980, CCX(3,19,340). The sole proven zero wire is q340; with the conservative abstract basis rank899 and 1 zero relation, no extra zero slot exists. A subsequent CNOT sourced by q340 at 41425048 has target q68 in the virtual quadratic expression. Simple deletion/virtualization is not justified. This is an obstruction to this packing strategy, not proof 900Q is minimal.
- #300/#303/#304/#310 reviewed; #310 full direct-mask adjoint 553704 paid and one fresh ordinary error, not competitive. #310 strict Lean 17 declarations passed; #308 and #311 local CI pass. No addition of prefix/component savings to full-tape counts.

## Reproduce
With exact parent KMB:
```sh
g++ -O3 -std=c++17 permute.cpp -o permute
g++ -O3 -std=c++17 root_frames.cpp -o root_frames
./permute joint.kmb intermediate.kmb
./root_frames intermediate.kmb final.kmb sites.tsv
sha256sum intermediate.kmb final.kmb
```
Full audit sources, native replay receipts and output KMB supplied in companion conversation archive. CI checks compiler and local Boolean identities only; no full oracle Lean certificate. Do not merge to main or submit this research candidate without additional independent validation.
