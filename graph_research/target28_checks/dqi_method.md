# DQI e4 endpoint scheduling screen

Input is the accepted e4 DQI member with SHA-256
`e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355`.
The [result](schedule.json) treats each endpoint's possible movement independently.
No altered program was emitted or sent to a verifier.

An initially zero optional interval starting at an unconditional X, CX or
CCX can tentatively start at the next target access, source write or scope
boundary. An unconditional R/HMR can tentatively move to just after the
last access to its quantum operand, its classical destination, or the last
condition-scope boundary. This gives an independent endpoint relaxation.
A simultaneous schedule needs an additional ordering proof for moving gates,
particularly when a later scrub and an earlier birth share a wire.

| Statistic | Original | Independent endpoint relaxation |
| --- | ---: | ---: |
| Width | 889 | 889 |
| Spans at maximum width | 1,570 | 1,490 |
| Operation positions at maximum width | 9,679,108 | 8,798,257 |

The scan shifted 24,615 births and 23,616 resets in the interval model.
The first remaining peak moves from 17,100,570 to 17,100,577. The report
does not bound width under arithmetic re-synthesis, value rematerialization,
or a general dependency reordering.

Latest available public portfolio manifest in the workspace records 97
costed DQI members. Best recorded cost is
`360209905486.0156` (821, Q889), and best recorded width-below-889 cost is
`398268953060.8457` (fe98, Q888). The existing e4 official pass cost is
`359707293756.04297`. This compares one downloaded catalogue snapshot.

## Reproduction

Use the unchanged e4 KMB, the pinned reset-separated interval table already
used by `graph_dqi/interval_cut.py`, and C++17.

```sh
g++ -O3 -std=c++17 score28_dqi/phase_schedule.cpp -o /tmp/dqi-phase-schedule
/tmp/dqi-phase-schedule "$DQI_E4_KMB" "$DQI_E4_INTERVALS" /tmp/dqi-e4-shifted.tsv
```
