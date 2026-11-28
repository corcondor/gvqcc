#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONHASHSEED=0
for name in map_cut capture prefix; do g++ -O3 -std=c++17 "$name.cpp" -o "$name"; done
g++ -O3 -std=c++17 joint_work/audit/replay.cpp -o replay
echo '2545a84896ba44152eab0db6856a056d23f60869c60fac8e7d1a8788c51e88dd  old.kmb' | sha256sum -c
echo 'b9f72a7bde001b81e0dc2530618dfa29815038b0bec7a542f75b2e3298d26870  new.kmb' | sha256sum -c
cut=$(./map_cut old.kmb new.kmb)
test "$cut" -eq 57227861
panel=joint_work/audit/saved.bin
./capture old.kmb "$panel" old_capture.bin 64572 36287888
./capture new.kmb "$panel" new_capture.bin 64572 "$cut"
./replay old.kmb "$panel" old_out.bin 64572
./prefix new.kmb new_prefix.kmb "$cut"
python3.12 native_prefix.py new_prefix.kmb "$panel" new_native_capture.bin
cmp new_capture.bin new_native_capture.bin
python3.12 native_prefix.py new.kmb "$panel" native_new_out.bin full
cd seam
export PYTHONPATH=".:..:${PYTHONPATH:-}"
python3.12 ../diagnose.py ../old_capture.bin ../new_native_capture.bin
python3.12 ../compare_frames.py
