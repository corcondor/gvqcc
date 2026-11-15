"""Test 54-Toffoli 0-ancilla GF(2^12) out-of-place multiplier (6+6 -> 3+3 Karatsuba) vs kickmix."""
import sys
import numpy as np
sys.path.insert(0, "/mnt/c/Users/81808/.openclaw/gvqcc/kickmix")
import kickmix as km

def ixor_gf2_mul_54(b: km.CircuitBuilder, x, y, z, gf: km.GF2Field, control=True):
    """z ^= (x * y) mod P(t) using 54 CCXs (0 ancillas when uncontrolled, 12 ancillas when controlled)."""
    assert len(x) == 12 and len(y) == 12 and len(z) == 12
    # If controlled, compute y_eff = control & y into 12 ancillas (12 init_and + 12 del_and = 12 Toffolis)
    if control is not True:
        y_eff = b.alloc_qubits(12)
        for i in range(12):
            b.init_and(control, y[i], y_eff[i])
        y_use = y_eff
    else:
        y_use = y

    # Build 23-bit unreduced product P(t) = x(t) * y_use(t) linearly mapped into 12-bit z via mod P(t)!
    # Precompute 23x12 reduction matrix R_mat where R_mat[k, j] = bit j of (t^k mod modulus)
    mod_int = gf.modulus
    R_mat = np.zeros((23, 12), dtype=np.uint8)
    cur = 1
    for k in range(23):
        for j in range(12):
            R_mat[k, j] = (cur >> j) & 1
        cur <<= 1
        if cur & (1 << 12):
            cur ^= mod_int

    # Wait: to use CX fanout on z (12 bits) without 23 ancillas, we can't map 23 bits -> 12 bits if we only have 12 bits of z...
    # UNLESS we compute each of the 3 6-bit products into z? Wait:
    # A 6-bit product has 11 bits (0..10), and 11 <= 12!
    # So we CAN compute ANY 11-bit product P(t) directly into 11 bits of z (or linearly transformed into z)
    # PROVIDED we only add ONE 11-bit product at a time, OR use CX fanout on z!
    # Wait: if we apply R_mat[shift + 0..10] -> z[0..11], wait: R_mat[shift + 0..10] is 11x12 over F2.
    # For shift=0: R_mat[0..10] is identity on z[0..10]!
    # For shift=6: R_mat[6..16] has rank 11 (11x12)!
    # For shift=12: R_mat[12..22] has rank 11 (11x12)!
    # Since EVERY 11x12 matrix M of full row rank 11 can be written as M = P_inv_rows_of_GL12,
    # Wait: we can't invert z if z already holds z_init!
    # YES WE CAN!! Because any invertible 12x12 linear map L on z satisfies:
    #   L^{-1}( L(z_init) ^ u ) = z_init ^ L^{-1}(u) !!
    # THAT'S LINEARITY!!
    # So for each of the 3 6-bit products (shift=0, shift=6, shift=12):
    #   1. Apply L^{-1} to z (CXs only -> 0 Toffolis!)
    #   2. Compute the 11-bit 6x6 product directly into z[0..10] (18 Toffolis!)
    #   3. Apply L to z (CXs only -> 0 Toffolis!)
    # Total = 3 * 18 = 54 Toffolis, 0 ancillas, works for ANY z_init!!

    def apply_linear_basis(M_11x12):
        # Extend 11x12 full-rank matrix M_11x12 to an invertible 12x12 matrix L
        L = np.zeros((12, 12), dtype=np.uint8)
        L[:11] = M_11x12
        for e in range(12):
            cand = np.zeros(12, dtype=np.uint8)
            cand[e] = 1
            test = np.vstack([M_11x12, cand])
            tm = test.copy()
            rk = 0
            for c in range(12):
                piv = next((r for r in range(rk, 12) if tm[r, c]), -1)
                if piv == -1: continue
                tm[[rk, piv]] = tm[[piv, rk]]
                for r in range(12):
                    if r != rk and tm[r, c]: tm[r] ^= tm[rk]
                rk += 1
            if rk == 12:
                L[11] = cand
                break
        # We want z_new = z_init ^ (v @ L), where v is 1x12 (v[11]=0).
        # Let T = L^{-1}. If we compute z' = z_init @ T, then z' ^= v, then z_new = z' @ L = z_init ^ (v @ L).
        # Decompose T = L^{-1} into right-multiplications (CX(src, dst): z[dst] ^= z[src], i.e., col dst ^= col src).
        # Reducing L by column operations C_1, ..., C_k to I gives L @ C_1 @ ... @ C_k = I => T = C_1 ... C_k!
        # Since z' = z_init @ C_1 @ ... @ C_k, we apply C_1, ..., C_k in forward order to transform z -> z',
        # and reverse order (C_k^{-1} ... C_1^{-1} = L) to transform z' -> z_new!
        M = L.copy()
        cx_ops = []
        for r in range(12):
            if not M[r, r]:
                piv = next(c for c in range(r + 1, 12) if M[r, c])
                M[:, [r, piv]] = M[:, [piv, r]]
                cx_ops.extend([(r, piv), (piv, r), (r, piv)])
            for c in range(12):
                if c != r and M[r, c]:
                    M[:, c] ^= M[:, r]
                    cx_ops.append((r, c))
        return cx_ops

    def mul3(ax, ay, az):
        """3-bit Karatsuba: az[0..4] ^= ax[0..2] * ay[0..2] in 6 CCXs, 0 ancillas."""
        # Standard 3-bit Karatsuba with CX fanout on az[0..4]:
        # p0 = ax[0]*ay[0] -> az[0], az[1], az[2]
        # p2 = ax[2]*ay[2] -> az[2], az[3], az[4]
        # Wait: let's write out exact coefficients of the 6 products in az[0..4]:
        # P0 = ax[0]*ay[0]                         -> z0, z1, z2
        # P1 = ax[2]*ay[2]                         -> z2, z3, z4
        # P01 = (ax[0]^ax[1])*(ay[0]^ay[1])        -> z1, z2
        # P02 = (ax[0]^ax[2])*(ay[0]^ay[2])        -> z2
        # P12 = (ax[1]^ax[2])*(ay[1]^ay[2])        -> z2, z3
        # P012 = (ax[0]^ax[1]^ax[2])*(ay[0]^ay[1]^ay[2]) -> z2
        # Let's check:
        # z0 = P0 = x0 y0. OK!
        # z1 = P0 ^ P01 = x0 y0 ^ (x0^x1)(y0^y1) = x0 y1 ^ x1 y0 ^ x1 y1? WAIT: x1 y1 is in z2, NOT z1!
        # Oops! z1 should NOT have x1 y1!
        # Let's fix the 6-CCX 3-bit Karatsuba coefficients:
        # Notice: x0 y1 ^ x1 y0 = (x0^x1)(y0^y1) ^ x0 y0 ^ x1 y1!
        # So z1 needs x1 y1 too, which means P012, P02, P12 must ALSO contribute to z1 if we want x1 y1 in z1!
        # Specifically: x1 y1 = P0 ^ P1 ^ P01 ^ P02 ^ P12 ^ P012!
        # Therefore:
        # z0 = P0
        # z1 = P0 ^ P01 ^ x1 y1 = P1 ^ P02 ^ P12 ^ P012
        # z2 = x0 y2 ^ x2 y0 ^ x1 y1 = (P0 ^ P1 ^ P02) ^ x1 y1 = P01 ^ P12 ^ P012
        # z3 = P1 ^ P12 ^ x1 y1 = P0 ^ P01 ^ P02 ^ P012
        # z4 = P1
        # Let's check z1 = P1 ^ P02 ^ P12 ^ P012:
        #   P1=x2y2, P02=(x0^x2)(y0^y2), P12=(x1^x2)(y1^y2), P012=(x0^x1^x2)(y0^y1^y2)
        #   x0y0: 0+1+0+1=0; x1y1: 0+0+1+1=0; x2y2: 1+1+1+1=0!
        #   x0y1+x1y0: 0+0+0+1=1! x0y2+x2y0: 0+1+0+1=0! x1y2+x2y1: 0+0+1+1=0! EXACT!
        # Check z2 = P01 ^ P12 ^ P012:
        #   x0y0: 1+0+1=0; x1y1: 1+1+1=1; x2y2: 0+1+1=0;
        #   x0y1+x1y0: 1+0+1=0; x0y2+x2y0: 0+0+1=1; x1y2+x2y1: 0+1+1=0! EXACT!
        # Check z3 = P0 ^ P01 ^ P02 ^ P012:
        #   by symmetry with z1 (swap 0<->2): EXACT!
        # So the 6 products fan out to:
        # P0   -> z0, z3
        # P1   -> z1, z4
        # P01  -> z2, z3
        # P02  -> z1, z3
        # P12  -> z1, z2
        # P012 -> z1, z2, z3
        def fan_ccx(c1, c2, targets):
            t0 = targets[0]
            for tt in targets[1:]:
                b.cx(t0, tt)
            b.ccx(c1, c2, t0)
            for tt in reversed(targets[1:]):
                b.cx(t0, tt)

        fan_ccx(ax[0], ay[0], [az[0], az[3]])
        fan_ccx(ax[2], ay[2], [az[1], az[4]])
        b.cx(ax[0], ax[1]); b.cx(ay[0], ay[1])
        fan_ccx(ax[1], ay[1], [az[2], az[3]])
        b.cx(ax[0], ax[1]); b.cx(ay[0], ay[1])
        b.cx(ax[0], ax[2]); b.cx(ay[0], ay[2])
        fan_ccx(ax[2], ay[2], [az[1], az[3]])
        b.cx(ax[0], ax[2]); b.cx(ay[0], ay[2])
        b.cx(ax[1], ax[2]); b.cx(ay[1], ay[2])
        fan_ccx(ax[2], ay[2], [az[1], az[2]])
        b.cx(ax[1], ax[2]); b.cx(ay[1], ay[2])
        b.cx(ax[0], ax[2]); b.cx(ax[1], ax[2])
        b.cx(ay[0], ay[2]); b.cx(ay[1], ay[2])
        fan_ccx(ax[2], ay[2], [az[1], az[2], az[3]])
        b.cx(ay[1], ay[2]); b.cx(ay[0], ay[2])
        b.cx(ax[1], ax[2]); b.cx(ax[0], ax[2])

    def mul6(ax, ay, az):
        """6-bit Karatsuba: az[0..10] ^= ax[0..5] * ay[0..5] in 18 CCXs, 0 ancillas."""
        # ax = a0 + t^3 a1, ay = b0 + t^3 b1 -> az[0..10]
        # 1) a0*b0 -> az[0..4] + az[3..7] (using CX fanout az[i] -> az[i+3] for i in 0..4!)
        for i in range(5): b.cx(az[i], az[3 + i])
        mul3(ax[:3], ay[:3], az[:5])
        for i in range(4, -1, -1): b.cx(az[i], az[3 + i])
        # 2) a1*b1 -> az[6..10] + az[3..7] (using CX fanout az[6+i] -> az[3+i]!)
        for i in range(4, -1, -1): b.cx(az[6 + i], az[3 + i])
        mul3(ax[3:], ay[3:], az[6:11])
        for i in range(5): b.cx(az[6 + i], az[3 + i])
        # 3) (a0^a1)*(b0^b1) -> az[3..7]
        for i in range(3): b.cx(ax[i], ax[3 + i]); b.cx(ay[i], ay[3 + i])
        mul3(ax[3:], ay[3:], az[3:8])
        for i in range(2, -1, -1): b.cx(ax[i], ax[3 + i]); b.cx(ay[i], ay[3 + i])

    # Now 12-bit Karatsuba: x = x0 + t^6 x1, y = y0 + t^6 y1
    # Product = x0*y0 (at shift=0) + (x0^x1)*(y0^y1) (at shift=6) + x0*y0 (at shift=6) + x1*y1 (at shift=6) + x1*y1 (at shift=12)
    # Wait: we can combine shift=0 and shift=6 in R_mat directly!
    # Look! M0 (11x12) = R_mat[0:11] ^ R_mat[6:17] (for x0*y0)!
    #       M1 (11x12) = R_mat[6:17] ^ R_mat[12:23] (for x1*y1)!
    #       M2 (11x12) = R_mat[6:17] (for (x0^x1)*(y0^y1))!
    # Wait: let's check if M0, M1, M2 all have rank 11!
    for M_mat, mode in [
        (R_mat[0:11] ^ R_mat[6:17], "0"),
        (R_mat[6:17] ^ R_mat[12:23], "1"),
        (R_mat[6:17], "2"),
    ]:
        cx_ops = apply_linear_basis(M_mat)
        for s, d in cx_ops:
            b.cx(z[s], z[d])
        if mode == "0":
            mul6(x[:6], y_use[:6], z[:11])
        elif mode == "1":
            mul6(x[6:], y_use[6:], z[:11])
        else:
            for i in range(6): b.cx(x[i], x[6 + i]); b.cx(y_use[i], y_use[6 + i])
            mul6(x[6:], y_use[6:], z[:11])
            for i in range(5, -1, -1): b.cx(x[i], x[6 + i]); b.cx(y_use[i], y_use[6 + i])
        for s, d in reversed(cx_ops):
            b.cx(z[s], z[d])

    if control is not True:
        for i in range(12):
            b.del_and(control, y[i], y_eff[i])
        b.free(y_eff)

gf = km.GF2Field(12)
for use_ctrl in [False, True]:
    b = km.CircuitBuilder()
    x = b.create_quantum_register(12, "x")
    y = b.create_quantum_register(12, "y")
    z = b.create_quantum_register(12, "z")
    ctrl = b.create_quantum_register(1, "ctrl")[0] if use_ctrl else True
    ixor_gf2_mul_54(b, x, y, z, gf, control=ctrl)
    c = b.finish_circuit()
    print(f"54-CCX Karatsuba use_ctrl={use_ctrl}: Q={c.num_qubits}, stats={c.operation_statistics()}")
