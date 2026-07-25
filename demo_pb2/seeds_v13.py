"""
seeds_v13.py — multi-seed error bars for the two headline PB-2 curves
(the paper's top blocker; see RESULTS_v13 caveats + queue.md #1).

Per seed s in 0..N-1:
  - NEW train/test split (queue P0 #4: vary the split for honest absolute
    CIs — the fixed-split caveat applied to all v13 numbers)
  - scaling sweep: train float net at nested corpus sizes, bake chips A/B
    with per-seed fab/write draws, eval k-RMSE + widened mel sample (40
    test utts vs 24)
  - drift series at full size: reuse the size-612 model, one FIXED
    per-device nu draw per seed used at every week (drift_head_nu) ->
    smooth monotonic aging per seed; the old per-week independent draws
    were the source of the gain-comp wiggle
No audio/demo rendering here — numbers only.

Outputs: results_v13_scaling_seeds.csv (seed x size)
         drift_v13_seeds.csv          (seed x week)
Run:  docker exec -w /workspace/demo_pb2 analog-nn-dev python3 seeds_v13.py
      (~5-6 min per seed on the Ryzen 3; 8 seeds ~45 min)
"""
import argparse
import csv
import time

import numpy as np

import tts_chip_sim_v7 as v7
import drift_v13 as dr
from train_scale_v13 import load_corpus, train_model, melspec_corr, P

SIZES = [36, 72, 144, 288, 480, 612]
EPOCHS, LR, BATCH = 250, 0.06, 256
N_MEL = 40           # widened from 24 (RESULTS_v13 caveat)
N_MEL_DRIFT = 20     # matches drift_series_v13


def eval_point(m, ceil, test_utts, Xte, Yte, Xtr, Ytr, seed):
    """Bake chips A/B with per-seed device draws; k-RMSE + melcorr(chip A)."""
    out = {}
    pf = m.forward(Xte)[-1]
    out["rmse_k_float"] = float(np.sqrt(((pf - Yte) ** 2).mean(axis=0))[:P].mean())
    chips = {}
    for name, cs in [("A", 1000 * seed + 100), ("B", 1000 * seed + 200)]:
        Wn, b3 = v7.bake_chip(m, np.random.default_rng(cs), Xtr, Ytr, ceil)
        o = v7.td_forward(m, Wn, Xte, v7.R_LEVELS,
                          np.random.default_rng(cs + 1), ceil, b3)
        out[f"rmse_k_chip{name}"] = float(
            np.sqrt(((o - Yte) ** 2).mean(axis=0))[:P].mean())
        chips[name] = (Wn, b3)
    WnA, b3A = chips["A"]
    have = [u for u in test_utts if u["audio"] is not None]
    step = max(1, len(have) // N_MEL)
    corrs = []
    for u in have[::step][:N_MEL]:
        O = v7.td_forward(m, WnA, u["X"], v7.R_LEVELS,
                          np.random.default_rng(7), ceil, b3A)
        corrs.append(melspec_corr(u["audio"], v7.synth_lpc(v7.from_outputs(O))))
    out["melcorr_chipA"] = float(np.nanmean(corrs))
    out["n_mel"] = len(corrs)
    return out


def drift_eval(m, Wn12, W3, b3, ceil, test_utts):
    corrs = []
    have = [u for u in test_utts if u["audio"] is not None][:N_MEL_DRIFT]
    for u in have:
        O = v7.td_forward(m, Wn12 + [W3], u["X"], v7.R_LEVELS,
                          np.random.default_rng(7), ceil, b3)
        corrs.append(melspec_corr(u["audio"], v7.synth_lpc(v7.from_outputs(O))))
    return float(np.nanmean(corrs))


def save(scal_rows, drift_rows):
    """Flush after every point — the host has crashed mid-run before."""
    for fn, rows in [("results_v13_scaling_seeds.csv", scal_rows),
                     ("drift_v13_seeds.csv", drift_rows)]:
        if rows:
            with open(fn, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--start", type=int, default=0)
    args = ap.parse_args()

    t0 = time.time()
    utts, PIDX = load_corpus()
    in_dim = utts[0]["X"].shape[1]
    print(f"loaded {len(utts)} utts  [{time.time()-t0:.0f}s]", flush=True)

    scal_rows, drift_rows = [], []
    for seed in range(args.start, args.start + args.seeds):
        ts = time.time()
        # per-seed utterance-level split (fixed split was a stated caveat)
        order = np.random.default_rng(seed).permutation(len(utts))
        n_test = int(round(0.15 * len(utts)))
        test_utts = [utts[i] for i in order[:n_test]]
        train_pool = [utts[i] for i in order[n_test:]]
        Xte = np.vstack([u["X"] for u in test_utts])
        Yte = np.vstack([u["Y"] for u in test_utts])

        m_full = None
        for sz in SIZES:
            tr = train_pool[:sz]
            Xtr = np.vstack([u["X"] for u in tr])
            Ytr = np.vstack([u["Y"] for u in tr])
            # lr 0.06 diverges for the odd init draw (NaN weights); retry
            # with a fresh stream and reduced lr rather than losing the seed
            for attempt in range(4):
                rng = np.random.default_rng(10_000 + 97 * seed + 31 * attempt)
                m = v7.Reg([in_dim, 64, 32, P + 3], rng)
                train_model(m, Xtr, Ytr, EPOCHS, LR * 0.6 ** attempt,
                            BATCH, rng)
                if all(np.isfinite(W).all() for W in m.W):
                    break
                print(f"seed {seed} size {sz}: diverged (attempt {attempt}),"
                      f" retrying at lr {LR * 0.6 ** (attempt + 1):.4f}",
                      flush=True)
            ceil = [np.percentile(h, 99.5) for h in m.forward(Xtr)[1:-1]]
            r = eval_point(m, ceil, test_utts, Xte, Yte, Xtr, Ytr, seed)
            r = {k: (round(v, 4) if isinstance(v, float) else v)
                 for k, v in r.items()}
            scal_rows.append(dict(seed=seed, corpus_size=sz, **r))
            print(f"seed {seed} size {sz:4d}: float {r['rmse_k_float']:.4f} "
                  f"chipA {r['rmse_k_chipA']:.4f} mel {r['melcorr_chipA']:.4f} "
                  f"[{time.time()-ts:.0f}s]", flush=True)
            if sz == SIZES[-1]:
                m_full, ceil_full, Xtr_f, Ytr_f = m, ceil, Xtr, Ytr
            save(scal_rows, drift_rows)

        # drift series on the full-size model, one nu draw per seed
        Wn12, Gp, Gn, s, b3 = dr.bake_head_full(
            m_full, np.random.default_rng(1000 * seed + 100),
            Xtr_f, Ytr_f, ceil_full)
        nrng = np.random.default_rng(77_000 + seed)
        nup = np.clip(nrng.normal(0.06, 0.012, Gp.shape), 1e-4, None)
        nun = np.clip(nrng.normal(0.06, 0.012, Gn.shape), 1e-4, None)
        base = drift_eval(m_full, Wn12, (Gp - Gn) * s, b3, ceil_full, test_utts)
        for wk in dr.weeks_grid():
            W3u = dr.drift_head_nu(Gp, Gn, s, wk, nup, nun, compensate=False)
            W3c = dr.drift_head_nu(Gp, Gn, s, wk, nup, nun, compensate=True)
            cu = drift_eval(m_full, Wn12, W3u, b3, ceil_full, test_utts)
            cc = drift_eval(m_full, Wn12, W3c, b3, ceil_full, test_utts)
            drift_rows.append(dict(seed=seed, weeks=wk,
                                   corr_uncomp=round(cu, 4),
                                   corr_gaincomp=round(cc, 4),
                                   corr_recal=round(base, 4)))
            print(f"seed {seed} week {wk:2d}: uncomp {cu:.4f} "
                  f"gain {cc:.4f} recal {base:.4f}", flush=True)
            save(scal_rows, drift_rows)

        save(scal_rows, drift_rows)
        print(f"== seed {seed} done [{time.time()-ts:.0f}s seed, "
              f"{time.time()-t0:.0f}s total]", flush=True)

    print(f"all done: {len(scal_rows)} scaling rows, {len(drift_rows)} drift "
          f"rows  [{time.time()-t0:.0f}s]", flush=True)


if __name__ == "__main__":
    main()
