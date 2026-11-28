# Gray72 -> packed-rank transfer (research only)

Reconstructed Gray72 donor SHA256 05a286d15697b67d27a6d376f4c927ba9a1f36686a93c997a446975946a335ca. Gray72 selector projected to classical-only prefix; no HMR or quantum-to-classical writes before cut. Exact public basis and degree-70 projection with strict support admission, and raw-moment phase compensation independent of S71.

Integrated native KMB: 900Q, 845690 classical bits, 518916679 instructions, static paid 12823738. Raw SHA256 917346ee37ecaa80b556cdca6cea3d5c84e175f9dcac13e6413806235716cbff. KickMix 1.0.0: 151 independent inputs, seeds 17 and 97, 302/302 successful, same simulator across scope-preserving selector and arithmetic chunks; final value, phase, ancillas and restored mask verified. Monolithic serialized KMB emitted and hash checked, but not loaded monolithically (memory limit). 149/151 admitted; aggregate residual zeros 8331 -> 26690; mean executed phase paid 679770 -> 650428.6754966887; integrated mean paid 12794396.675496688 on mixed panel, not an official score. This is NOT a competitive replacement for the 316k low-cost decoder.

Direct low-cost bypass attempt rejected: degree<=70 polynomial masks already handled by original Gray72; no paid improvement, extra classical instructions. Known inherited errors remain.

Proof scope: exact degree<=70 gauge pairing/repayment, mask restoration, support admission and conditional cost; imported PR339 rank/residual lemmas. No claim of all-input native implementation proof or official verifier pass. Do not merge into submission branch.
