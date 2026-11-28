# Complete-circuit live tensor transport (research only)

Base: #306 review at ed19ff69e4fb1ce5a71f0d92d575313a1c71353a. #306's 18-member archive is in the owner's Library, not in the GitHub tree. The new executable accepts any exact complete KMB file; the CI inputs below are the available pinned #279 DQI donor and #180 C1/3266.5 non-DQI families, not the #306 8-anchor or latest chemistry/InvSqrt binaries. Do not identify these older donors as the latest score candidate.

## Transfer of prior mathematics

- #280/#305: affine transport in both control and target directions. For fixed guard and target/control-disjoint block, if the target affine map so far is M and a product updates target j, pull back its output vector by M^{-1} e_j. Move all nonlinear contributions to entry and replay the original affine gates. Control linear forms include the constant term.
- #283/#284/#299/#302: after exact Boolean square-free expansion, group the quadratic tensor by shared control; factor each target-by-control binary matrix. A dirty-target echo realizes one rank-one output direction with one CCX, without extra quantum wires. Try three deterministic pivot orientations; independently check every tensor coefficient.
- #293/#297/#302: early HMR on a write-only target tail and exact debt dualization at each original update position. Do not cross another reset/measurement, scope boundary, any read of the target, or access to the measured classical bit. Move no rotation relative to another rotation.
- #295/#297: adjacent common-factor CCZ and mixed CCX/CCZ phase bridge.
- #202/#303: conservative clean-lifetime packing. Pin all registered quantum IDs. Release only provably zero scratch, including unconditional reset/HMR. No assumption about conditional resets.

## Actual preliminary experiment (not a new physical score)

Read #180 invsqrt_C1.zip from pinned GitHub commit 08d01e2c18365000dec61e3403f5342452c69855, decoded its exact complete 49,825-op 37Q KMB. Independent JS analyses:
- 606 same-guard affine/quadratic interval attempts; 70 valid disjoint-target tensor blocks; no strictly lower-rank block found. This is a bounded search.
- Early HMR and contiguous commuting guard-rank scan: zero paid savings.
- Exact-expression conservative zero-lifetime analysis: 22 pinned x wires, 15 peak scratch, peak at operation 302; no 36Q claim.
- Symbolic live-span scan found three inactive CCZ (already recorded in #305); not expected-cost improvement.

The new C++ compiler and five local Lean statements are provided for actual whole-tape CI. Do not claim new paid reduction, complete oracle proof, new official score, private-salt result, or a zero-error DQI until observed. The #279 donor retains low-weight defects; paired preservation of existing failures is not correctness. #296 ghost projection and #303 balanced Padé are not transplanted into incompatible ABIs. The 24,820 prefix CCX saving and #304 prefix savings are excluded from all full-circuit accounting.

CI uses actual pinned full artifacts and reports each gate family, width, operation count, SHA and matched evaluation. For DQI the panel is a bounded matched native regression (2,048 ordinary plus structured stress), not the full competition shot count. InvSqrt tests every legal x once, chemistry tests 64 shots/address. Keep #292/#306 and main untouched; research only, no submission.
