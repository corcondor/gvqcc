"""Verify ixor_gf2_mul_54 bit-for-bit against gf.mul on 2000 random inputs."""
import sys
import numpy as np
sys.path.insert(0, "/mnt/c/Users/81808/.openclaw/gvqcc/kickmix")
import kickmix as km
from test_54ccx_gf2mul import ixor_gf2_mul_54

gf = km.GF2Field(12)
b = km.CircuitBuilder()
x = b.create_quantum_register(12, "x")
y = b.create_quantum_register(12, "y")
z = b.create_quantum_register(12, "z")
ixor_gf2_mul_54(b, x, y, z, gf, control=True)
c = b.finish_circuit()
c.to_file("/tmp/gf_mul54.kmx")

# Parse gates and simulate 2000 random (x, y, z_init) in vectorized numpy!
with open("/tmp/gf_mul54.kmx") as f:
    ops = [ln.strip().split() for ln in f if ln.strip() and not ln.startswith("REGISTER") and not ln.startswith("APPEND")]

rng = np.random.default_rng(123)
N = 2000
x_vals = rng.integers(0, 4096, size=N, dtype=np.int32)
y_vals = rng.integers(0, 4096, size=N, dtype=np.int32)
z_vals = rng.integers(0, 4096, size=N, dtype=np.int32)

state = np.zeros((36, N), dtype=np.uint8)
for i in range(12):
    state[i] = (x_vals >> i) & 1
    state[12 + i] = (y_vals >> i) & 1
    state[24 + i] = (z_vals >> i) & 1

for op in ops:
    if op[0] == "CX":
        s, d = int(op[1][1:]), int(op[2][1:])
        state[d] ^= state[s]
    elif op[0] == "CCX":
        c1, c2, t = int(op[1][1:]), int(op[2][1:]), int(op[3][1:])
        state[t] ^= (state[c1] & state[c2])
    else:
        raise ValueError(f"Unexpected op: {op}")

x_out = sum((state[i].astype(np.int32) << i) for i in range(12))
y_out = sum((state[12 + i].astype(np.int32) << i) for i in range(12))
z_out = sum((state[24 + i].astype(np.int32) << i) for i in range(12))

assert np.all(x_out == x_vals), "x modified!"
assert np.all(y_out == y_vals), "y modified!"
errs = 0
for k in range(N):
    expected = int(z_vals[k]) ^ gf.mul(int(x_vals[k]), int(y_vals[k]))
    if int(z_out[k]) != expected:
        errs += 1
        if errs <= 5:
            print(f"Mismatch at {k}: x={x_vals[k]}, y={y_vals[k]}, z={z_vals[k]}, got={z_out[k]}, exp={expected}")
print(f"Verified {N} random inputs: errors={errs}")
