#!/bin/sh
# Rebuild the 95-product head loaders for another words table (e.g. after re-valued dead words in the batches they
# see).  usage: rebuild_heads95.sh WORDS.npz NREL E k [k ...]   (k from 1 5 7 11; NREL E = 11 29 gives 234,
# 12 29 gives 233).  Per loader: design search for a 95-product cover (minutes), then window search (see run234.sh).
# Output: best_angle_k_<k>.kmb in a fresh work directory next to this script.  Uses 3 threads.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
WORDS=$(cd "$(dirname "$1")" && pwd)/$(basename "$1"); shift
NREL=$1; E=$2; shift 2
TAG=$(sha256sum "$WORDS" | cut -c1-10)
DIR="$HERE/rebuild_$TAG"
mkdir -p "$DIR"
cp "$HERE"/*.py "$HERE"/*.exe "$HERE"/run234.sh "$DIR"/
export K8_NPZ=$(cygpath -w "$WORDS" 2>/dev/null || echo "$WORDS")
cd "$DIR"
for k in "$@"; do
  python -X utf8 x43_perp.py "$k" > "perp_k$k.txt"
  ./d20.exe 20 900 1 3 < "perp_k$k.txt" > "d20_k$k.out" 2> "d20_k$k.err"
  grep -q FOUND "d20_k$k.out" || { echo "no 95-product design for loader $k"; continue; }
  python -X utf8 x46_fix7.py "$k" "$E" || { echo "no usable 95-product cover for loader $k"; continue; }
  sh run234.sh "$NREL" "$E" 600 "$k"
done
ls -l best_angle_k_*.kmb
