"""Test if 1-LSB flips (K=1..100) on angle_words improve (lam_eff, err1, err2)."""
import pathlib, sys
import numpy as np
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, "/mnt/c/Users/81808/.openclaw/gvqcc/verifiers")
from dfthcsos.scoreinfra import dfthc_math

ref_dir = pathlib.Path.home() / "gvqcc_work" / "ref"
pre = np.load(ref_dir / "precomputed.npz")
h1_base = pre["h1_base"]; T_mat = pre["T_mat"]; T_norm2 = float(pre["T_norm2"])
beta_1 = float(pre["beta_1"]); ecore = float(pre["ecore"]); electrons = int(pre["electrons"])
E_upper = -22140.27335

sub_dir = pathlib.Path("/mnt/c/Users/81808/.openclaw/gvqcc/sub_unpacked/dfthcsos")
sub = dict(np.load(sub_dir / "submission.npz"))
tree_edges = sub["tree_edges"].astype(np.int64)
R, B, C = sub["W"].shape
N = 76; RC = R * C; A_tot = N + R * B

pol = np.load(pathlib.Path.home() / "gvqcc_work" / "submission_alt_polished.npz")
words = pol["angle_words"].astype(np.int64).copy()
w = pol["W"].copy().astype(np.float64)
w_B = pol["H2_I"].copy().astype(np.float64)

def words_to_angles(wd):
    return (wd % 256).astype(np.float64) / 128.0

def forward_u_with_cache(angles):
    vectors = np.zeros((A_tot, N), dtype=np.float64)
    vectors[:, 0] = 1.0
    cache = []
    for k, (p, ch) in enumerate(tree_edges):
        pv = vectors[:, p].copy(); cv = vectors[:, ch].copy()
        th = np.pi * angles[:, k]; co, si = np.cos(th), np.sin(th)
        npv = co * pv - si * cv; ncv = si * pv + co * cv
        vectors[:, p] = npv; vectors[:, ch] = ncv
        cache.append((p, ch, co, si, npv, ncv))
    return vectors, cache

def backward_u(g_vectors, cache):
    g_v = g_vectors.copy()
    g_angles = np.zeros((A_tot, N - 1), dtype=np.float64)
    for k in range(len(cache) - 1, -1, -1):
        p, ch, co, si, npv, ncv = cache[k]
        gp, gc = g_v[:, p].copy(), g_v[:, ch].copy()
        g_angles[:, k] = np.pi * (-ncv * gp + npv * gc)
        g_v[:, p] = co * gp + si * gc; g_v[:, ch] = -si * gp + co * gc
    return g_angles

def eval_all(angles, wc, wBc):
    u_all, u_cache = forward_u_with_cache(angles)
    one_body_vecs = u_all[:N]
    u_b_rho = u_all[N:].reshape(R, B, N)
    M = np.einsum("rbp,rbq->rbpq", u_b_rho, u_b_rho)
    W_rho_c = wBc - np.sum(wc, axis=1)
    X = np.einsum("rbc,rbpq->rcpq", wc, M)
    WX = np.einsum("rc,rcpq->pq", W_rho_c, X)
    h1_prime = h1_base - WX
    evals, evecs = np.linalg.eigh(h1_prime)
    overlaps = np.abs(one_body_vecs @ evecs)
    q_idx, i_idx = linear_sum_assignment(-overlaps)
    matched_evals = np.empty_like(evals); matched_evals[q_idx] = evals[i_idx]
    diff1 = np.einsum("j,jp,jq->pq", matched_evals, one_body_vecs, one_body_vecs) - h1_prime
    err1 = float(np.linalg.norm(diff1))
    g1_norm = diff1 / max(err1, 1e-30)
    v_q = one_body_vecs[q_idx]; c_i = np.sum((v_q @ g1_norm) * v_q, axis=1); E_matched = evecs[:, i_idx]
    g_err1_WX = -((E_matched * c_i[None, :]) @ E_matched.T - g1_norm)
    g_one_body = np.zeros_like(one_body_vecs); g_one_body[q_idx] = 2.0 * matched_evals[q_idx, None] * (v_q @ g1_norm)
    Xf = X.reshape(RC, N * N); A = Xf @ Xf.T; XT = Xf @ T_mat
    err2 = float(np.sqrt(max(float(np.sum(A * A)) - 2.0 * float(np.sum(XT * Xf)) + T_norm2, 0.0)))
    g_err2_X = ((2.0 / max(err2, 1e-30)) * (A @ Xf - XT)).reshape(R, C, N, N)
    lam_h1 = float(np.sum(np.abs(evals))); sgn_ev = np.sign(evals)
    w_l1 = np.sum(np.abs(wc), axis=1); s_rc = w_l1 + np.abs(wBc)
    Lambda = lam_h1 + 0.25 * float(np.sum(s_rc ** 2))
    E_sos = ecore - electrons * beta_1 - (lam_h1 - float(np.sum(evals))) - 0.5 * float(np.sum(W_rho_c ** 2))
    E_gap = E_upper - E_sos
    lam_eff = float(np.sqrt(max(E_gap * (2.0 * Lambda - E_gap), 1e-12)))
    d_leff_d_egap = (Lambda - E_gap) / lam_eff; d_leff_d_Lam = E_gap / lam_eff
    g_lamh1_h1 = (evecs * sgn_ev[None, :]) @ evecs.T
    g_egap_WX = -(g_lamh1_h1 - np.eye(N)); g_Lam_WX = -g_lamh1_h1
    def back_WX(g_WX):
        gX = np.einsum("rc,pq->rcpq", W_rho_c, g_WX)
        gM = np.einsum("rbc,rcpq->rbpq", wc, gX)
        gM_sym = 0.5 * (gM + np.swapaxes(gM, -1, -2))
        return 2.0 * np.einsum("rbpq,rbq->rbp", gM_sym, u_b_rho)
    g_err1_u2 = back_WX(g_err1_WX)
    gM2 = np.einsum("rbc,rcpq->rbpq", wc, g_err2_X)
    g_err2_u2 = 2.0 * np.einsum("rbpq,rbq->rbp", 0.5 * (gM2 + np.swapaxes(gM2, -1, -2)), u_b_rho)
    g_leff_u2 = d_leff_d_egap * back_WX(g_egap_WX) + d_leff_d_Lam * back_WX(g_Lam_WX)
    def to_ga(g1b, g2b):
        gu = np.zeros((A_tot, N), dtype=np.float64)
        if g1b is not None: gu[:N] = g1b
        gu[N:] = g2b.reshape(R * B, N)
        return backward_u(gu, u_cache)
    return lam_eff, err1, err2, to_ga(None, g_leff_u2), to_ga(g_one_body, g_err1_u2), to_ga(None, g_err2_u2)

le0, e10, e20, ga_le, ga_e1, ga_e2 = eval_all(words_to_angles(words), w, w_B)
print(f"Base: lam_eff={le0:.6f}, err1={e10*1e3:.4f} mHa, err2={e20*1e3:.4f} mHa", flush=True)
g_comb = ga_le + 500.0 * ga_e1 + 500.0 * ga_e2
flat = np.argsort(-np.abs(g_comb).ravel())
for K in [1, 3, 10, 30, 100]:
    cand = words.copy()
    rows, cols = np.unravel_index(flat[:K], words.shape)
    cand[rows, cols] = (cand[rows, cols] - np.sign(g_comb[rows, cols]).astype(np.int64)) % 256
    le, e1, e2, *_ = eval_all(words_to_angles(cand), w, w_B)
    print(f"  K={K:3d}: lam_eff={le:.6f}, err1={e1*1e3:.4f} mHa, err2={e2*1e3:.4f} mHa", flush=True)
