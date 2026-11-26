# V79: width-parametric conditional carrier transport (research only)
Refs #163, #168, #169, #92, #160, #162, #167. Complete native invsqrt width sweep. 28 actual KMBs (14 controls and 14 candidates) are included with the compiler and independent replayer in the companion ZIP GVQCC_V79_Width23to36_WholeCircuit_RESEARCH_ONLY.zip; SHA256 a1439ab581e4f6140577f293b47678eacb5427e456ec3fa63217a8cf5d4d157a.
 
|Q|CCX control|CCX candidate|ops control|ops candidate|generic R control|generic R candidate|formula cost candidate|
|---:|---:|---:|---:|---:|---:|---:|---:|
|23|6144|3800|37031|34719|12923|12923|2518758.45|
|24|4416|4390|58449|58391|7681|7681|1593938.61|
|25|3904|3708|61742|61097|7681|7747|1656961.16|
|26|3545|3052|62027|61017|7681|7747|1706183.61|
|27|3302|2673|61317|60504|7681|7747|1761573.06|
|28|3057|2365|60739|59643|7681|7747|1818192.50|
|29|2875|2134|60141|58700|7681|7747|1876428.95|
|30|2730|1964|59333|58151|7681|7747|1936033.40|
|31|2589|1793|58361|57356|7681|7747|1995266.84|
|32|2460|1654|58058|56402|7681|7747|2055182.29|
|33|2353|1539|57217|55852|7681|7747|2115611.74|
|34|2261|1428|56474|55285|7681|7747|2175947.18|
|35|2200|1341|56184|54479|7681|7747|2236900.63|
|36|2151|1267|55558|53942|7681|7747|2298148.08|

24Q control is V78; other controls are newly emitted same-specification alternatives, NOT the historical best at every width. 25Q/26Q formula costs increase against these new controls (R+66); 12 other widths improve all CCX, ops, and formula cost. All 28 KMBs passed independent serialized full-cube replay on 2^22 inputs, exact HMR sign coefficients, exact uint128 phase contraction, restoration, legal 3,133,452 input tolerance; common absolute margin 138112178. The 36Q result also reduces the recorded #168 spectral CCX 1355 to 1267; do not conflate lineages or add savings. 22Q already has a zero-CCX diagnostic #92. No 37Q new candidates. No new DQI or chemistry experiment, official KickMix or score change. 

Algorithm: resident conditional flag span f*V transports intersections with CNOT basis changes, HMR erases the complement. First flag materialized in a basis slot instead of reserving an independent wire. Joint trie partition DP trades prefix lifetime against capacity. Narrow widths use shortest path across mixed-depth prefix predicates and exact complementary child toggles. Sources are the actual multiwidth.py, treewidth.py, tourwidth.py, tour24orig.py in companion archive; this PR provides local algebra proof source and measurement ledger, not the whole compiler. Local proof is not whole-circuit formalization.

References: Amy/Azimzadeh/Mosca arXiv:1712.01859; Amy/Lunderville doi:10.1145/3704873; Khattar/Gidney doi:10.22331/q-2025-05-21-1752; Khattar et al. arXiv:2610.23832; Yang/Yuan arXiv:2611.02345. Motivated by parity network and conditional clean/HMR synthesis; no full reproduction of those papers claimed.
