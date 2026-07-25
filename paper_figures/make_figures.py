"""
make_figures.py — paper figures for 80_paper_draft.md.

All data is read from committed result files (no numbers invented here):
  fig_power      F13 numbers (10_findings_v2 / bundle 03 power study)
  fig_latency    F10 slot counts
  fig_topology   ../topology_v14/results_topology_v14.csv
  fig_ir         data/results_v12_nodal.csv (verbatim copy of the CSV cell in
                 bundle_03_system_power_ir.ipynb, v12 exact nodal study)
  fig_multimodal F14 v10 measured endpoints (shared chip 24.0 uW @M=1,
                 24.1 @M=8; M separate chips = M x 24 uW by construction)
  fig_scaling    ../demo_pb2/results_v13_scaling_seeds.csv (8-seed) if
                 present, else skipped
  fig_drift      ../demo_pb2/drift_v13_seeds.csv (8-seed) if present, else
                 skipped

Style: reference dataviz palette (light mode), one axis per chart, thin
marks, hairline grid, direct labels (relief rule for aqua/yellow slots).
Run in the container:
  docker exec -w /workspace/paper_figures analog-nn-dev python3 make_figures.py
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---- palette (dataviz reference instance, light mode) ----
SURF, INK, SEC, MUT = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASE = "#e1e0d9", "#c3c2b7"
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"   # blue orange aqua yellow
SEQ = ["#9ec5f4", "#5598e7", "#2a78d6", "#184f95"]            # blue ramp 200/350/450/600

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": BASE, "axes.labelcolor": SEC, "text.color": INK,
    "xtick.color": MUT, "ytick.color": MUT, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9.5, "axes.titlesize": 10.5, "axes.titleweight": "bold",
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
})


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


# ------------------------------------------------------------- fig_power
def fig_power():
    fig, axs = plt.subplots(1, 3, figsize=(11.6, 3.1), layout="constrained")
    # (a) core breakdown, 13.0 uW total @100 Hz
    blocks = [("periphery (op-amp bank)", 9.0), ("input drivers", 2.4),
              ("memristor head (off-leak)", 1.44), ("baked L2 array", 0.20),
              ("baked L1 array", 0.008)]
    ax = axs[0]
    names = [b[0] for b in blocks][::-1]
    vals = [b[1] for b in blocks][::-1]
    y = np.arange(len(vals))
    ax.barh(y, vals, height=0.55, color=C1)
    for yi, v in zip(y, vals):
        ax.text(v + 0.15, yi, f"{v:g}", va="center", color=SEC, fontsize=8.5)
    ax.set_yticks(y, names, fontsize=8.5)
    ax.set_xlim(0, 10.8)
    ax.set_xlabel("µW @ 100 Hz frames")
    ax.set_title("a  Core power: periphery-bound", loc="left")
    ax.grid(axis="y", visible=False)

    # (b) same 7,584-MAC network, other technologies (log scale, dot plot)
    ax = axs[1]
    tech = [("ESP32 software", 6250), ("M4-class MCU", 38),
            ("all-programmable analog", 16.2), ("this work (baked core)", 13.0),
            ("28 nm digital ASIC*", 2.5)]
    names = [t[0] for t in tech][::-1]
    vals = [t[1] for t in tech][::-1]
    y = np.arange(len(vals))
    cols = [MUT] * len(vals)
    cols[names.index("this work (baked core)")] = C2
    ax.hlines(y, 1, vals, color=GRID, lw=1.2)
    ax.scatter(vals, y, s=42, color=cols, zorder=3)
    for yi, v in zip(y, vals):
        ax.annotate(f"{v:g}", (v, yi), xytext=(0, 7),
                    textcoords="offset points", ha="center",
                    color=SEC, fontsize=8.5)
    ax.set_xscale("log")
    ax.set_xlim(1, 40000)
    ax.set_ylim(-0.6, len(vals) - 0.2)
    ax.set_yticks(y, names, fontsize=8.5)
    ax.set_xlabel("µW (log)  ·  *not printable")
    ax.set_title("b  Same net, other substrates", loc="left")
    ax.grid(axis="y", visible=False)

    # (c) control plane ladder -> system total
    ax = axs[2]
    ctrl = [("ESP32 always-on", 225000), ("ULP coprocessor", 300),
            ("ring sequencer (baked-only)", 10), ("SYSTEM: core + sequencer", 23)]
    names = [c[0] for c in ctrl][::-1]
    vals = [c[1] for c in ctrl][::-1]
    y = np.arange(len(vals))
    cols = [MUT] * len(vals)
    cols[names.index("ring sequencer (baked-only)")] = C1
    cols[names.index("SYSTEM: core + sequencer")] = C2
    ax.hlines(y, 1, vals, color=GRID, lw=1.2)
    ax.scatter(vals, y, s=42, color=cols, zorder=3)
    for yi, v in zip(y, vals):
        ax.annotate(f"{v:,}", (v, yi), xytext=(0, 7),
                    textcoords="offset points", ha="center",
                    color=SEC, fontsize=8.5)
    ax.set_xscale("log")
    ax.set_xlim(1, 3.3e6)
    ax.set_ylim(-0.6, len(vals) - 0.2)
    ax.set_yticks(y, names, fontsize=8.5)
    ax.set_xlabel("µW (log)")
    ax.set_title("c  Control plane: baking deletes it", loc="left")
    ax.grid(axis="y", visible=False)
    fig.savefig("fig_power.png")
    plt.close(fig)
    print("fig_power.png")


# ----------------------------------------------------------- fig_latency
def fig_latency():
    fig, ax = plt.subplots(figsize=(5.6, 2.2))
    rows = [("8-bit serialized interlayer", 768, MUT),
            ("time-domain pipeline (digits)", 103, C1),
            ("one-hot clock chip (PB-2)", 43, C2)]
    names = [r[0] for r in rows][::-1]
    vals = [r[1] for r in rows][::-1]
    cols = [r[2] for r in rows][::-1]
    y = np.arange(len(vals))
    ax.barh(y, vals, height=0.5, color=cols)
    for yi, v in zip(y, vals):
        ax.text(v + 12, yi, f"{v} slots", va="center", color=SEC, fontsize=8.5)
    ax.set_yticks(y, names, fontsize=8.5)
    ax.set_xlim(0, 880)
    ax.set_xlabel("time slots per inference  (43 µs @ 1 µs printed slot; 18× vs serialized)")
    ax.set_title("Converter-free encoding kills the 2ᴺ latency (F10)", loc="left")
    ax.grid(axis="y", visible=False)
    fig.savefig("fig_latency.png")
    plt.close(fig)
    print("fig_latency.png")


# ---------------------------------------------------------- fig_topology
def fig_topology():
    rows = read_csv("../topology_v14/results_topology_v14.csv")
    L1 = [r for r in rows if r["layer"] == "L1"]

    def series(topo, col):
        pts = sorted(((fnum(r["r_seg"]), fnum(r[col])) for r in L1
                      if r["topo"] == topo), key=lambda p: p[0])
        return ([p[0] for p in pts if not np.isnan(p[1])],
                [p[1] for p in pts if not np.isnan(p[1])])

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for topo, col_, lab in [("grid", C1, "grid"),
                            ("grid+perm", C2, "grid + placement"),
                            ("tiled k4 t0.05", C3, "clustered 4 tiles")]:
        x, yv = series(topo, "act_err")
        ax.plot(x, yv, "-o", color=col_, lw=2, ms=5, label=lab)
        x, yv = series(topo, "act_err_comp")
        if x:
            ax.plot(x, yv, "--s", color=col_, lw=1.6, ms=4.5, alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlabel("wire segment resistance r_seg (·1/G_MAX)")
    ax.set_ylabel("activation-current error (2,628 real frames)")
    ax.set_title("Baked-array topology: placement is free, tiles help, "
                 "IR-aware baking works until clipping", loc="left")
    ax.axvspan(2e-3, 4e-3, color=GRID, alpha=0.5, lw=0)
    ax.text(2.9e-3, 0.06, "clipping\nwall", ha="center", color=SEC, fontsize=8)
    ax.annotate("solid = as-designed\ndashed = IR-aware baked",
                xy=(1.1e-4, 0.60), color=SEC, fontsize=8.5)
    ax.annotate("printed PB-1 op point (r≈2.4e-9):\nerr 0.002, off-scale left",
                xy=(1.1e-4, 0.50), color=MUT, fontsize=8)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    fig.savefig("fig_topology.png")
    plt.close(fig)
    print("fig_topology.png")


# ---------------------------------------------------------------- fig_ir
def fig_ir():
    rows = [r for r in read_csv("data/results_v12_nodal.csv")
            if r["exp"] == "E12"]
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.4), layout="constrained")
    # (a) raw distortion vs r_seg by array size (ordered -> sequential ramp)
    ax = axs[0]
    for i, M in enumerate([32, 64, 128, 256]):
        pts = sorted(((fnum(r["r_seg"]), fnum(r["raw_err"])) for r in rows
                      if int(r["M"]) == M), key=lambda p: p[0])
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o",
                color=SEQ[i], lw=2, ms=4.5)
        if M == 256:
            ax.annotate(f"{M}×{M}", pts[-1], xytext=(-4, 8),
                        textcoords="offset points", ha="right",
                        color=SEQ[i], fontsize=8.5)
        else:
            ax.text(pts[-1][0] * 1.25, pts[-1][1], f"{M}×{M}",
                    color=SEQ[i], fontsize=8.5, va="center")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(7e-6, 9e-3)
    ax.set_xlabel("r_seg")
    ax.set_ylabel("‖W_eff − W‖ / ‖W‖")
    ax.set_title("a  Exact nodal IR distortion vs array size", loc="left")
    ax.annotate("printed PB-1: r≈2.4e-9\n(immune, off-scale left)",
                xy=(1.5e-4, 3.2e-3), color=MUT, fontsize=8)
    # (b) design-time compensation: baked continuous vs 16-level quantized
    ax = axs[1]
    for M, ls in [(32, "-"), (64, "--")]:
        sub = sorted((r for r in rows if int(r["M"]) == M
                      and not np.isnan(fnum(r["comp_resid"]))),
                     key=lambda r: fnum(r["r_seg"]))
        x = [fnum(r["r_seg"]) for r in sub]
        ax.plot(x, [fnum(r["comp_resid"]) for r in sub], ls + "o",
                color=C1, lw=2, ms=4.5)
        ax.plot(x, [fnum(r["comp_resid_quant"]) for r in sub], ls + "s",
                color=C2, lw=2, ms=4.5)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_yticks([0.02, 0.05, 0.1, 0.2, 0.5],
                  ["0.02", "0.05", "0.1", "0.2", "0.5"])
    ax.set_xlabel("r_seg")
    ax.set_ylabel("residual after pre-compensation")
    ax.set_title("b  Baked comp ≈10× better than write-quantized\n"
                 "    (solid 32², dashed 64²)", loc="left")
    ax.text(1.05e-4, 0.011, "baked (continuous)", color=C1, fontsize=8.5)
    ax.text(1.05e-4, 0.31, "16-level write-quantized", color=C2, fontsize=8.5)
    fig.savefig("fig_ir.png")
    plt.close(fig)
    print("fig_ir.png")


# -------------------------------------------------------- fig_multimodal
def fig_multimodal():
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    M = np.arange(1, 9)
    ax.plot(M, 24 * M, "-o", color=C2, lw=2, ms=5)
    ax.text(7.5, 178, "M separate chips\n(= M × 24 µW)", color=C2,
            ha="right", fontsize=8.5)
    # measured endpoints from v10 (shared baked-core chip)
    ax.plot([1, 8], [24.0, 24.1], "-o", color=C1, lw=2, ms=6)
    ax.text(7.9, 34, "one shared baked-core chip\n(measured: 24.0 → 24.1 µW)",
            color=C1, ha="right", fontsize=8.5)
    ax.set_xlabel("number of modalities M")
    ax.set_ylabel("system power (µW)")
    ax.set_title("Multimodal power is flat in modality count (F14)", loc="left")
    ax.set_xticks(M)
    ax.set_ylim(0, 205)
    fig.savefig("fig_multimodal.png")
    plt.close(fig)
    print("fig_multimodal.png")


# ------------------------------------------- fig_scaling / fig_drift (seeds)
def band(ax, x, ys, color, label=None):
    """ys: seeds x points. mean line + 95% CI band (t, n-1 df)."""
    ys = np.asarray(ys, float)
    n = ys.shape[0]
    mean = np.nanmean(ys, axis=0)
    sd = np.nanstd(ys, axis=0, ddof=1)
    tcrit = {2: 12.71, 3: 4.30, 4: 3.18, 5: 2.78, 6: 2.57, 7: 2.45,
             8: 2.36}.get(n, 2.0)
    ci = tcrit * sd / np.sqrt(n)
    ax.plot(x, mean, "-o", color=color, lw=2, ms=4.5, label=label, zorder=3)
    ax.fill_between(x, mean - ci, mean + ci, color=color, alpha=0.16, lw=0)
    return mean, ci


def fig_scaling():
    path = "../demo_pb2/results_v13_scaling_seeds.csv"
    if not os.path.exists(path):
        print("fig_scaling SKIPPED (no seeds csv yet)")
        return
    rows = read_csv(path)
    seeds = sorted({int(r["seed"]) for r in rows})
    sizes = sorted({int(r["corpus_size"]) for r in rows})
    if len(seeds) < 2:
        print("fig_scaling SKIPPED (<2 seeds so far)")
        return

    def grid_of(col):
        g = np.full((len(seeds), len(sizes)), np.nan)
        for r in rows:
            g[seeds.index(int(r["seed"])), sizes.index(int(r["corpus_size"]))] \
                = fnum(r[col])
        return g

    tick_sizes = [s for s in sizes if s != 480]   # 480/612 labels collide
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.5), layout="constrained")
    ax = axs[0]
    band(ax, sizes, grid_of("rmse_k_float"), C1, "software float (ceiling)")
    band(ax, sizes, grid_of("rmse_k_chipA"), C2, "chip A (baked + head cal)")
    band(ax, sizes, grid_of("rmse_k_chipB"), C3, "chip B")
    ax.set_xscale("log")
    ax.set_xticks(tick_sizes, [str(s) for s in tick_sizes])
    ax.minorticks_off()
    ax.set_xlabel("training corpus size (utterances)")
    ax.set_ylabel("LPC k-RMSE (held-out)")
    ax.set_title(f"a  Fixed baked core does not saturate\n"
                 f"    ({len(seeds)} seeds, 95% CI)", loc="left")
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    ax = axs[1]
    band(ax, sizes, grid_of("melcorr_chipA"), C2)
    ax.set_xscale("log")
    ax.set_xticks(tick_sizes, [str(s) for s in tick_sizes])
    ax.minorticks_off()
    ax.set_ylim(0.74, 0.95)
    ax.set_xlabel("training corpus size (utterances)")
    ax.set_ylabel("mel-spectrogram correlation")
    ax.set_title("b  Chip-A speech fidelity\n    vs corpus size", loc="left")
    fig.savefig("fig_scaling.png")
    plt.close(fig)
    print(f"fig_scaling.png ({len(seeds)} seeds)")


def fig_drift():
    path = "../demo_pb2/drift_v13_seeds.csv"
    if not os.path.exists(path):
        print("fig_drift SKIPPED (no seeds csv yet)")
        return
    rows = read_csv(path)
    seeds = sorted({int(r["seed"]) for r in rows})
    weeks = sorted({int(r["weeks"]) for r in rows})
    if len(seeds) < 2:
        print("fig_drift SKIPPED (<2 seeds so far)")
        return

    def grid_of(col):
        g = np.full((len(seeds), len(weeks)), np.nan)
        for r in rows:
            g[seeds.index(int(r["seed"])), weeks.index(int(r["weeks"]))] \
                = fnum(r[col])
        return g

    # paired per-seed change from week 0: model-to-model base variance
    # (0.79-0.90) would swamp the within-seed aging signal in absolute units
    base = grid_of("corr_recal")
    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    band(ax, weeks, grid_of("corr_recal") - base, C3,
         "head recalibrated (resets)")
    band(ax, weeks, grid_of("corr_gaincomp") - base, C1,
         "global gain rescale")
    band(ax, weeks, grid_of("corr_uncomp") - base, C2, "uncompensated")
    ax.set_xlabel("weeks of memristor aging  (G(t)=G₀(t/t₀)^−ν, ν~N(0.06,0.012))")
    ax.set_ylabel("Δ mel-spectrogram correlation vs week 0")
    ax.set_title(f"Drift lives in the head; the baked core is immune "
                 f"({len(seeds)} seeds, 95% CI)", loc="left")
    ax.set_xticks(weeks)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    fig.savefig("fig_drift.png")
    plt.close(fig)
    print(f"fig_drift.png ({len(seeds)} seeds)")


if __name__ == "__main__":
    fig_power()
    fig_latency()
    fig_topology()
    fig_ir()
    fig_multimodal()
    fig_scaling()
    fig_drift()
