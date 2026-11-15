"""Enumerate tag-preserving block permutations and export mixed-rank inputs."""
from argparse import ArgumentParser
from hashlib import sha256
from itertools import combinations, product
from pathlib import Path
import json
import numpy as np

TAG_PAIRS = [(0,1),(0,2),(1,2),(0,3),(1,3)]
N = 1220


def tags(x):
    return sum((((x >> a) & (x >> b)) & 1) << i for i,(a,b) in enumerate(TAG_PAIRS))


def tag_preserving_permutations():
    vectors = [x for x in range(16) if tags(x) == 0]
    for c, *columns in product(vectors, repeat=5):
        images = tuple(c ^ sum_xor(columns[j] for j in range(4) if (i >> j) & 1)
                       for i in range(16))
        if len(set(images)) == 16 and all(tags(i) == tags(x) for i, x in enumerate(images)):
            yield images


def sum_xor(values):
    y = 0
    for x in values:
        y ^= x
    return y


def group(i):
    return -1 if i < 76 else (i - 76) // 143


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("recovered_words", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    words = np.load(args.recovered_words, allow_pickle=False)[:N].astype(np.uint8)
    assert words.shape == (N,75)
    digest = sha256(words.tobytes()).hexdigest()
    assert digest == "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
    batches = words.reshape(N,15,5)
    delta = np.bitwise_xor(batches, np.concatenate((np.zeros_like(batches[:,:1]),batches[:,:-1]),axis=1))
    delta ^= (delta & 64) << 1
    planes = (delta[...,None] >> np.arange(8,dtype=np.uint8)).reshape(N,600) & 1
    identity = tuple(range(16))
    affine = sorted(tag_preserving_permutations())
    assert affine[0] == identity
    swaps = []
    for a,b in combinations(range(16),2):
        if tags(a) == tags(b):
            p = list(identity)
            p[a],p[b] = p[b],p[a]
            swaps.append(tuple(p))
    perm = [identity, *swaps]
    moves = [q for q in range(76) if group(16*q) == group(16*q + 15)]
    with args.out.open("w") as file:
        file.write(f"{len(perm)} {len(moves)}\n")
        for values in perm:
            file.write(" ".join(map(str,values))+"\n")
        file.write(" ".join(map(str,moves))+"\n")
        raw = planes[:1216].reshape(76,16,600)
        for block in raw:
            domain = block[1:] ^ block[:1]
            packed = ((domain.astype(np.uint16)) << np.arange(15,dtype=np.uint16)[:,None]).sum(0)
            file.write(" ".join(map(str,packed.tolist()))+"\n")
    print(json.dumps({"tag_preserving_affine_maps":len(affine),
                      "tag_preserving_transpositions":len(swaps),"movable_complete_blocks":len(moves),
                      "individual_outputs":600,"candidate_addresses":len(moves)*16,
                      "screened_addresses":1216,"words_sha256":digest}))


if __name__ == "__main__":
    main()
