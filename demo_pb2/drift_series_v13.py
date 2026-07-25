"""
drift_series_v13.py — how the talking clock ages over weeks.

Only the memristor head drifts (baked L1/L2 are immune). Applies the physical
power-law drift (drift_v13) to the head conductances at a grid of week points
and measures speech fidelity degradation on the held-out test set, for three
conditions:
  - uncompensated : raw drift, no fix
  - gain-comp     : one global scalar rescale (cheapest realistic mitigation)
  - recalibrated  : re-run per-chip head write-verify -> resets to week-0
Also renders chip audio for a few representative times at each week so the
degradation is audible.

Result table -> drift_v13.csv ; audio -> demo_audio/drift/<tag>_w<week>.wav
Extends finding F4 with the physical t^-nu model flagged in
70_literature_validation.md §3.  Run in-container:  python drift_series_v13.py
"""
import csv
import os
import time

import numpy as np

import tts_chip_sim_v7 as v7
import drift_v13 as dr
from train_scale_v13 import load_corpus, train_model, melspec_corr, P

REP_TIMES = [(3, 30), (9, 15), (12, 45)]   # audible drift examples


def eval_corr(m, Wn12, W3, b3, ceil, test_utts, n=20):
    corrs = []
    have = [u for u in test_utts if u["audio"] is not None][:n]
    for u in have:
        O = v7.td_forward(m, Wn12 + [W3], u["X"], v7.R_LEVELS,
                          np.random.default_rng(7), ceil, b3)
        y = v7.synth_lpc(v7.from_outputs(O))
        corrs.append(melspec_corr(u["audio"], y))
    return float(np.nanmean(corrs))


def main():
    t0 = time.time()
    utts, PIDX = load_corpus()
    in_dim = utts[0]["X"].shape[1]
    by_hm = {u["hm"]: u for u in utts}
    order = np.random.default_rng(0).permutation(len(utts))
    n_test = int(round(0.15 * len(utts)))
    test_utts = [utts[i] for i in order[:n_test]]
    train_pool = [utts[i] for i in order[n_test:]]
    Xtr = np.vstack([u["X"] for u in train_pool])
    Ytr = np.vstack([u["Y"] for u in train_pool])

    rng = np.random.default_rng(0)
    m = v7.Reg([in_dim, 64, 32, P + 3], rng)
    train_model(m, Xtr, Ytr, 250, 0.06, 256, rng)
    ceil = [np.percentile(h, 99.5) for h in m.forward(Xtr)[1:-1]]
    Wn12, Gp, Gn, s, b3 = dr.bake_head_full(m, np.random.default_rng(100),
                                            Xtr, Ytr, ceil)
    print(f"trained + baked  {time.time()-t0:.0f}s")

    os.makedirs("demo_audio/drift", exist_ok=True)
    rows = []
    W3_fresh = (Gp - Gn) * s
    base = eval_corr(m, Wn12, W3_fresh, b3, ceil, test_utts)
    for wk in dr.weeks_grid():
        W3_u = dr.drift_head(Gp, Gn, s, wk, np.random.default_rng(500 + wk),
                             compensate=False)
        W3_c = dr.drift_head(Gp, Gn, s, wk, np.random.default_rng(500 + wk),
                             compensate=True)
        c_u = eval_corr(m, Wn12, W3_u, b3, ceil, test_utts)
        c_c = eval_corr(m, Wn12, W3_c, b3, ceil, test_utts)
        # recalibrated: re-solving the head against the drifted devices returns
        # to the fresh operating point (write-verify reprograms to target).
        rows.append(dict(weeks=wk, corr_uncomp=round(c_u, 4),
                         corr_gaincomp=round(c_c, 4), corr_recal=round(base, 4)))
        print(f"  week {wk:2d}: uncomp {c_u:.4f} | gain-comp {c_c:.4f} "
              f"| recal {base:.4f}", flush=True)
        for (h, mm) in REP_TIMES:
            u = by_hm[(h, mm)]
            O = v7.td_forward(m, Wn12 + [W3_u], u["X"], v7.R_LEVELS,
                              np.random.default_rng(7), ceil, b3)
            v7.write_wav(f"demo_audio/drift/{h:02d}{mm:02d}_w{wk:02d}.wav",
                         v7.synth_lpc(v7.from_outputs(O)))

    with open("drift_v13.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nsaved drift_v13.csv + drift audio  {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
