"""
topology_v14.py — is a grid the best arrangement for the BAKED sections?

Question (Avery, 2026-07-25): in the fixed/baked part of the chip, can a
non-grid topology — clustering groups of weights, changing wire lengths —
shrink the array or beat the plain crossbar on IR distortion? And since the
nodal solve makes IR drop exactly predictable (F15 linearity theorem:
ohmic array + ideal drivers + virtual ground => W_eff is exact and
input-independent), can we BUILD the model using the predicted IR
(layout-aware pre-compensation)?

Three experiments, all on the real trained PB-2 baked weights
(demo_pb2/demo_v13_data.json, L1 92x64 and L2 64x32), driven by the real
one-hot frames / activations from the showcase utterances:

  T1 PLACEMENT (free): row/col permutation of the same grid. Wordline
     resistance accumulates with column index, bitline resistance with
     distance from the sense edge -> put high-conductance columns near the
     drivers and high-conductance (and frequently-driven) rows near the
     sense amps. Zero hardware cost; function unchanged (permutation is
     just routing order).
  T2 CLUSTERED TILES (shrinks): k-means co-cluster output columns by which
     input rows they actually use (binary mask of |W|>theta, weighted);
     prune sub-threshold cells (a printed resistor you simply don't print);
     drop rows a tile doesn't use (row compaction) -> each tile is a
     smaller crossbar with shorter word/bitlines. Tile outputs join on a
     short bus into the shared virtual-ground integrator (modeled as extra
     series R on the sense). Metrics: exact W_eff distortion, activation-
     current error on real drive patterns, device count, footprint area,
     total wire length.
  T3 IR-AWARE BAKING: design-time pre-compensation (F15 fixed point run
     per-topology) — bake conductances such that the PREDICTED W_eff of
     this layout equals the target. Continuous (baked) only; report
     residual + conductance-clipping fraction.

Model notes / honesty:
  - Solver is verbatim nodal_ir_v12 (bundle 03): differential planes share
    wordlines (worst-case loading), r_seg in units of 1/G_MAX per segment
    at unit pitch; drivers/sense 1e4 (near-ideal).
  - Activation-current error is measured in the CURRENT domain (X @ W_eff
    vs X @ W_ideal, relative RMS). Biases are added by the periphery and
    ReLU happens in the integrator, so array IR only touches this term.
    Pruning cost is folded in because reference is the UNPRUNED W.
  - Inter-tile wordline routing overhead is charged to the wire-length
    metric (routing factor), not to the electrical model: wordlines drive
    voltage, and with near-ideal drivers their extra length matters far
    less than bitline length; stated as a model assumption.
  - PB-1 printed operating point is r_seg ~ 2.4e-9 (IR-immune by
    construction, F15). This study matters for the DENSER/lower-R regimes:
    sputtered thin-film cores, research arrays, or if the printed pitch
    shrinks. We sweep r_seg = 1e-4 .. 3e-3 to expose the differences.

Run (container):  docker exec -w /workspace/topology_v14 analog-nn-dev \
                  python3 topology_v14.py
Outputs: results_topology_v14.csv + stdout log.
"""
import json
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

t0 = time.time()
rng = np.random.default_rng(0)

# ---------------------------------------------------------------- solver
# verbatim from nodal_ir_v12.py (bundle 03, F15), plus per-call sense
# conductance so tile join-bus series resistance can be modeled.
G_DRV = 1e4
G_SNS = 1e4


def build_lu(Gp, Gn, r_seg, g_sns=G_SNS):
    M, N = Gp.shape
    G = np.concatenate([Gp, Gn], axis=1)
    NN = 2 * N
    g_seg = 1.0 / max(r_seg, 1e-12)
    nw = M * NN
    wid = (np.arange(M)[:, None] * NN + np.arange(NN)[None, :])
    bidx = nw + wid
    a1 = wid[:, :-1].ravel(); b1 = wid[:, 1:].ravel()
    g1 = np.full(a1.size, g_seg)
    mask = G.ravel() > 1e-12
    a2 = wid.ravel()[mask]; b2 = bidx.ravel()[mask]; g2 = G.ravel()[mask]
    a3 = bidx[:-1, :].ravel(); b3 = bidx[1:, :].ravel()
    g3 = np.full(a3.size, g_seg)
    A_ = np.concatenate([a1, a2, a3]); B_ = np.concatenate([b1, b2, b3])
    Gv = np.concatenate([g1, g2, g3])
    nn = 2 * nw
    diag = np.zeros(nn)
    np.add.at(diag, A_, Gv); np.add.at(diag, B_, Gv)
    np.add.at(diag, wid[:, 0], G_DRV)
    np.add.at(diag, bidx[-1, :], g_sns)
    rows = np.concatenate([A_, B_, np.arange(nn)])
    cols = np.concatenate([B_, A_, np.arange(nn)])
    vals = np.concatenate([-Gv, -Gv, diag])
    A = sp.csc_matrix((vals, (rows, cols)), shape=(nn, nn))
    return spl.splu(A), wid, bidx, nw, NN


def solve_weff(Gp, Gn, r_seg, g_sns=G_SNS):
    M, N = Gp.shape
    lu, wid, bidx, nw, NN = build_lu(Gp, Gn, r_seg, g_sns)
    RHS = np.zeros((2 * nw, M))
    RHS[wid[:, 0], np.arange(M)] = G_DRV
    X = lu.solve(RHS)
    I = g_sns * X[bidx[-1, :], :]
    return (I[:N, :] - I[N:, :]).T


def to_pair(W):
    s = np.abs(W).max() + 1e-12
    return np.clip(W, 0, None) / s, np.clip(-W, 0, None) / s, s


# ------------------------------------------------- topology descriptions
# A layout = list of tiles. Tile = dict(rows=<row idx array>, cols=<col idx
# array>, join_len=<segments of join bus to the integrator>).
# W_eff assembly: full MxN zeros, each tile contributes its exact nodal
# solve; join bus modeled as series R lowering effective sense conductance.

def tile_weff(W, tile, r_seg):
    sub = W[np.ix_(tile["rows"], tile["cols"])]
    Gp, Gn, s = to_pair(sub)
    g_sns = 1.0 / (r_seg * tile.get("join_len", 0) + 1.0 / G_SNS)
    return solve_weff(Gp, Gn, r_seg, g_sns) * s


def layout_weff(W, layout, r_seg):
    Weff = np.zeros_like(W)
    for tile in layout:
        Weff[np.ix_(tile["rows"], tile["cols"])] = tile_weff(W, tile, r_seg)
    return Weff


def layout_metrics(layout, M, N):
    """device count, footprint area (cell sites), wire length (segments,
    differential 2x cols; join bus + a 1.15x inter-tile routing factor)."""
    area = sum(len(t["rows"]) * len(t["cols"]) for t in layout)
    wire = 0.0
    for t in layout:
        R, C = len(t["rows"]), len(t["cols"])
        wire += R * 2 * C + 2 * C * R          # wordlines + differential bitlines
        wire += 2 * C * t.get("join_len", 0)   # join bus
    if len(layout) > 1:
        wire *= 1.15                           # inter-tile routing overhead
    grid_area = M * N
    grid_wire = M * 2 * N + 2 * N * M
    return area / grid_area, wire / grid_wire


def grid_layout(M, N):
    return [dict(rows=np.arange(M), cols=np.arange(N), join_len=0)]


def perm_layout(W, row_drive=None):
    """Placement-only optimization. Wordline R grows with col index j,
    bitline R with distance from sense (last row) -> heavy columns to low
    j, heavy (and frequently driven) rows to high i."""
    M, N = W.shape
    col_order = np.argsort(-np.abs(W).sum(axis=0))          # heavy cols first
    w = np.abs(W).sum(axis=1)
    if row_drive is not None:
        w = w * (0.5 + row_drive / (row_drive.max() + 1e-12))
    row_order = np.argsort(w)                                # heavy rows LAST (near sense)
    return [dict(rows=row_order, cols=col_order, join_len=0)]


def clustered_layout(W, k, theta_rel, row_drive=None, perm=True, seed=0):
    """k tiles by column co-clustering on pruned row-usage masks; row
    compaction per tile. theta_rel: prune |W| < theta_rel*max|W|."""
    from sklearn.cluster import KMeans
    M, N = W.shape
    th = theta_rel * np.abs(W).max()
    mask = np.abs(W) > th                                    # M x N survives
    feat = (mask * np.abs(W)).T                              # N x M
    km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(feat)
    layout, join_acc = [], 0
    for c in range(k):
        cols = np.flatnonzero(km.labels_ == c)
        if cols.size == 0:
            continue
        rows = np.flatnonzero(mask[:, cols].any(axis=1))
        if rows.size == 0:
            continue
        if perm:
            sub = np.abs(W[np.ix_(rows, cols)])
            co = np.argsort(-sub.sum(axis=0)); cols = cols[co]
            w = sub.sum(axis=1)
            if row_drive is not None:
                w = w * (0.5 + row_drive[rows] / (row_drive.max() + 1e-12))
            ro = np.argsort(w); rows = rows[ro]
        layout.append(dict(rows=rows, cols=cols, join_len=join_acc))
        join_acc += 2 * len(cols)          # bus runs past earlier tiles
    return layout, th


def prune(W, th):
    Wp = W.copy()
    Wp[np.abs(Wp) < th] = 0.0
    return Wp


# ------------------------------------------------ IR-aware pre-compensation
def precompensate_layout(W_target, layout, r_seg, iters=4):
    """F15 fixed point per tile: scale conductances until the PREDICTED
    W_eff of this layout matches the target. Continuous (baked) values.
    Returns (Weff_after, residual_rel, clip_frac)."""
    Weff = np.zeros_like(W_target)
    clipped, total = 0, 0
    for tile in layout:
        tgt = W_target[np.ix_(tile["rows"], tile["cols"])]
        Gp, Gn, s = to_pair(tgt)
        tp = np.clip(tgt / s, 0, None); tn = np.clip(-tgt / s, 0, None)
        g_sns = 1.0 / (r_seg * tile.get("join_len", 0) + 1.0 / G_SNS)
        for _ in range(iters):
            Wp = solve_weff(Gp, np.zeros_like(Gn), r_seg, g_sns)
            Wn = solve_weff(Gn, np.zeros_like(Gp), r_seg, g_sns)
            with np.errstate(divide="ignore", invalid="ignore"):
                fp = np.where(Wp > 1e-9, tp / Wp, 1.0)
                fn = np.where(Wn > 1e-9, tn / Wn, 1.0)
            Gp = np.clip(Gp * np.clip(fp, 0.5, 2.0), 0, 1.0)
            Gn = np.clip(Gn * np.clip(fn, 0.5, 2.0), 0, 1.0)
        clipped += int(((Gp > 0.999) | (Gn > 0.999)).sum()); total += Gp.size * 2
        Weff[np.ix_(tile["rows"], tile["cols"])] = solve_weff(Gp, Gn, r_seg, g_sns) * s
    res = np.linalg.norm(Weff - W_target) / (np.linalg.norm(W_target) + 1e-12)
    return Weff, res, clipped / max(total, 1)


# ---------------------------------------------------------------- data
D = json.load(open("../demo_pb2/demo_v13_data.json"))
W1 = np.array(D["layers"][0]["W"])          # 92 x 64 baked, chip-A (fab noise incl.)
W2 = np.array(D["layers"][1]["W"])          # 64 x 32 baked

# real drive patterns from the showcase utterances
X1_rows, A1_rows = [], []
drive_count = np.zeros(W1.shape[0])
for u in D["utterances"]:
    for idx in u["frames"]["input"]:
        x = np.zeros(W1.shape[0]); x[idx] = 1.0
        X1_rows.append(x); drive_count[idx] += 1
    A1_rows.extend(u["frames"]["a1"])
X1 = np.array(X1_rows)                       # frames x 92 (one-hot sets)
A1 = np.array(A1_rows)                       # frames x 64 (real L1 outputs)
print(f"loaded weights {W1.shape}/{W2.shape}, {len(X1)} real frames "
      f"[{time.time()-t0:.0f}s]", flush=True)


def act_err(X, Weff, Wref):
    Yr = X @ Wref
    return float(np.linalg.norm(X @ Weff - Yr) / (np.linalg.norm(Yr) + 1e-12))


# ---------------------------------------------------------------- sweep
R_SEGS = [1e-4, 1e-3, 3e-3]
COMP_R = {1e-3, 3e-3}
results = []


def run(layer, name, W, Wtgt, layout, X, drive, r_seg, do_comp):
    Weff = layout_weff(Wtgt, layout, r_seg)
    raw = np.linalg.norm(Weff - W) / np.linalg.norm(W)
    a_raw = act_err(X, Weff, W)
    area, wire = layout_metrics(layout, *W.shape)
    ndev = int(sum((np.abs(Wtgt[np.ix_(t['rows'], t['cols'])]) > 1e-12).sum()
                   for t in layout)) * 2
    row = dict(layer=layer, topo=name, r_seg=r_seg,
               raw_err=round(float(raw), 4), act_err=round(a_raw, 4),
               area_rel=round(area, 3), wire_rel=round(wire, 3), n_dev=ndev,
               comp_resid=np.nan, comp_clip=np.nan, act_err_comp=np.nan)
    if do_comp and r_seg in COMP_R:
        # compensation target: the ORIGINAL W (so compensation also repairs
        # pruning error where surviving devices can absorb it)
        tgt = np.zeros_like(W)
        for t in layout:
            tgt[np.ix_(t["rows"], t["cols"])] = W[np.ix_(t["rows"], t["cols"])]
        Wc, res, clip = precompensate_layout(tgt, layout, r_seg)
        row.update(comp_resid=round(res, 4), comp_clip=round(clip, 4),
                   act_err_comp=round(act_err(X, Wc, W), 4))
    results.append(row)
    print(f"[{layer}] {name:24s} r={r_seg:g}: Weff err {raw:.3f} "
          f"act {a_raw:.3f} area {area:.2f} wire {wire:.2f}"
          + (f" | comp {row['comp_resid']:.4f} (clip {row['comp_clip']:.1%}) "
             f"act {row['act_err_comp']:.3f}"
             if not np.isnan(row["comp_resid"]) else "")
          + f"  [{time.time()-t0:.0f}s]", flush=True)


# ---- L1 (92x64, one-hot drive) ----
gl = grid_layout(*W1.shape)
pl = perm_layout(W1, drive_count)
for r in R_SEGS:
    run("L1", "grid", W1, W1, gl, X1, drive_count, r, True)
    run("L1", "grid+perm", W1, W1, pl, X1, drive_count, r, True)

for th_rel in [0.05, 0.10, 0.20]:
    th = th_rel * np.abs(W1).max()
    W1p = prune(W1, th)
    pr_err = np.linalg.norm(W1p - W1) / np.linalg.norm(W1)
    print(f"-- theta={th_rel}: pruned {100*(1-(np.abs(W1)>th).mean()):.0f}% of "
          f"cells, prune-only err {pr_err:.3f}", flush=True)
    # pruned grid control (no shrink, same devices removed)
    for r in R_SEGS:
        run("L1", f"grid_pruned t{th_rel}", W1, W1p, gl, X1, drive_count, r, False)
    for k in [2, 4]:
        lay, _ = clustered_layout(W1, k, th_rel, drive_count, perm=True)
        for r in R_SEGS:
            run("L1", f"tiled k{k} t{th_rel}", W1, W1p, lay, X1, drive_count, r, True)

# ---- L2 (64x32, real a1 drive) ----
gl2 = grid_layout(*W2.shape)
pl2 = perm_layout(W2, A1.sum(axis=0))
lay2, th2 = clustered_layout(W2, 2, 0.10, A1.sum(axis=0), perm=True)
W2p = prune(W2, th2)
for r in R_SEGS:
    run("L2", "grid", W2, W2, gl2, A1, None, r, True)
    run("L2", "grid+perm", W2, W2, pl2, A1, None, r, True)
    run("L2", "tiled k2 t0.1", W2, W2p, lay2, A1, None, r, True)

# ---- printed operating point sanity check (PB-1 board, F15) ----
Weff_p = layout_weff(W1, gl, 2.4e-9)
print(f"printed op-point r=2.4e-9 grid: Weff err "
      f"{np.linalg.norm(Weff_p-W1)/np.linalg.norm(W1):.2e} (immune, as F15)",
      flush=True)

import csv
with open("results_topology_v14.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    w.writeheader(); w.writerows(results)
print(f"\nwrote results_topology_v14.csv ({len(results)} rows) "
      f"[{time.time()-t0:.0f}s total]", flush=True)
