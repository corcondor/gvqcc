# 13-wire successor seam audit
Research only. No complete 899Q candidate, no score claim.

This audit reads the pre-#312 exact #299 Joint donor (SHA-256 a8b5c62e24e7e44818bd46d75f8fa00a2bb9de64965c8c07912637dd58d7ebea). The gate indices in the #314 allocator log are on that donor, not on the shortened #312 output. Rebuild the local TSV data with the native.hpp reader in PR #312 (`research/dqi_whole_root_frame/native.hpp`).

    g++ -std=c++17 -O3 view.cpp -o view
    ./view joint.kmb 41425167 41425302 > seam.tsv
    ./view joint.kmb 41425267 41440000 > after.tsv
    python probe.py
    python tunnel.py

Run with KickMix 1.0.0 and NumPy. The isolated block's emitted 13-bit representative is drop10(s) XOR bit10(s)*2632. The compact mask is 2632, obtained by deleting bit 10 of 5704. KMB serialization and native replay passed 8192 input states and both HMR outcomes. The HMR bit is supplied independently in the replacement test. A standalone clean-wire HMR also generated both outcomes; whole-tape placement and outcome stream are not certified.

The 385 actual operations following the replaced measurement were also included. The state difference lives on logical wires 46, 104, 294, 631. It reaches exactly one phase observer, Z(q46) conditioned on the same b49612, cancelling the early measurement phase replacement. The combined local replay therefore omits the two entry phase gates, preserving the later Z(q46) verbatim. Output remains encoded; no conversion to the colliding old representation is attempted. The combined native replay includes all 8192 entries with randomized other wires and matched measurement results. The affine difference and phase analysis is independent of those other wires' values.

The next product block reuses q340 at 41425653. Continuing across the following gate 41425674 using one direction invisible to every intervening CCX control is impossible. The six control rows in compact entry coordinates are 2, 1032, 128, 256, 32, 426; their XOR is 1024. Thus if they all vanish on the direction, its required missing coordinate 10 is zero. This is an exact obstruction for the single-direction model, not a lower bound for nonlinear reframing or a joint resynthesis of the two product blocks.

Independent PR #313 check: the pinned successful workflow (run 46147187999, artifact 15264765744) built a complete 898Q circuit, 533579 static paid, SHA-256 918dc05dd4222435e5824b526774cea4ae13895917e29982aeacf9d62456a5e6. Replayed with the exact PR #314 panels and native KickMix: 0/1024 ordinary, 0/622 archived, 0/144 dense weight-stratified errors (value, phase, ancillas, and public mask checked), with a mean of 533189.279296875 on the ordinary panel. This is a correctness reference on the tested cases, not a lower-cost contender or proof for all inputs.
