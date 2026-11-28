import sys
import numpy as np

sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc\verifiers")
import kickmix as km

w_3284 = np.load(r"c:\Users\81808\.openclaw\gvqcc_v2832\sub_3284\dfthcsos\submission.npz")["angle_words"]
w_3301 = np.load(r"c:\Users\81808\.openclaw\gvqcc_v2832\v68_planner\out\b13_for_207_out\family\submission.npz")["angle_words"]

tot3284 = tot3301 = min_sum = 0
print(" k |  3284 |  3301 |   min | diff_words_batch_k")
print("---+-------+-------+-------+-------------------")
for k in range(15):
    c1 = km.Circuit.from_file(rf"c:\Users\81808\.openclaw\gvqcc_v2832\sub_3284\dfthcsos\angle_k_{k}.kmb")
    c2 = km.Circuit.from_file(rf"c:\Users\81808\.openclaw\gvqcc_v2832\v68_planner\out\b13_for_207_out\family\angle_k_{k}.kmb")
    n1 = sum(1 for l in str(c1).splitlines() if l.startswith("CCX "))
    n2 = sum(1 for l in str(c2).splitlines() if l.startswith("CCX "))
    dw = int((w_3284[:, 5*k:5*(k+1)] != w_3301[:, 5*k:5*(k+1)]).sum())
    tot3284 += n1
    tot3301 += n2
    min_sum += min(n1, n2)
    print(f"{k:2d} | {n1:5d} | {n2:5d} | {min(n1, n2):5d} | {dw:18d}")
print("---+-------+-------+-------+-------------------")
print(f"SUM| {tot3284:5d} | {tot3301:5d} | {min_sum:5d} |")
