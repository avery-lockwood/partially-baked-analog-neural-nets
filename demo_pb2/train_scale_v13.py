"""
train_scale_v13.py — the PB-2 headline experiment.

Question (the design law at scale): as the shared talking-clock corpus grows
36 -> 720 utterances with a FIXED baked-core architecture, does spectrogram
fidelity hold (the baked core generalizes across the larger shared
vocabulary) or degrade (the fixed core saturates)? The fidelity-vs-corpus-
size curve is the paper figure.

Pipeline (reuses the validated v7 core verbatim; see PROVENANCE.md):
  corpus_v13.npz  ->  one-hot phone-context encoding (v7.encode_frames)
  fixed 85/15 utterance-level train/test split
  for each corpus size (nested prefixes of the train pool):
     train float Reg[in,64,32,13]  (LPC-weighted MSE, v7 math)
     bake chip A/B  (per-chip ridge head calibration, v7.bake_chip)
     eval on the FIXED test set: LPC-feature RMSE + 24-mel log-spectrogram
       correlation of chip-A resynthesis vs. the original MBROLA audio
  -> results_v13_scaling.csv
At full size, also render demo wavs for a spread of times + viz_data.json.

Runs in the container (numpy/scipy; espeak/mbrola only needed upstream to
build the corpus). Configurable so the weak Ryzen 3 stays tractable:
  python train_scale_v13.py --epochs 250 --batch 256
  python train_scale_v13.py --sizes 72,180,360,540,720 --quick
"""
import argparse
import csv
import json
import os
import time

import numpy as np

import tts_chip_sim_v7 as v7

CORPUS = "corpus_v13.npz"
P = v7.P  # 10 LPC reflection coeffs


# ---------------- metric: 24-mel log-spectrogram correlation ----------------
def mel_bank(fs, nfft, nmel):
    # Slaney-style triangular mel filterbank (from trimodal_v11.mel_bank)
    m = lambda f: 2595 * np.log10(1 + f / 700)
    mi = lambda x: 700 * (10 ** (x / 2595) - 1)
    e = mi(np.linspace(m(80), m(min(7500, fs / 2 - 100)), nmel + 2))
    fr = np.fft.rfftfreq(nfft, 1 / fs)
    B = np.zeros((nmel, len(fr)))
    for k in range(nmel):
        l, c, r = e[k], e[k + 1], e[k + 2]
        B[k] = np.clip(np.minimum((fr - l) / (c - l + 1e-9),
                                  (r - fr) / (r - c + 1e-9)), 0, None)
    return B


def logmel(y, fs=v7.FS, nfft=512, hop=128, nmel=24):
    win = np.hanning(nfft)
    n = max(0, 1 + (len(y) - nfft) // hop)
    S = np.zeros((n, nfft // 2 + 1))
    for i in range(n):
        seg = y[i * hop:i * hop + nfft] * win
        S[i] = np.abs(np.fft.rfft(seg)) ** 2
    B = mel_bank(fs, nfft, nmel)
    return np.log(S @ B.T + 1e-6)


def melspec_corr(y_ref, y_test):
    A, Bm = logmel(y_ref), logmel(y_test)
    n = min(len(A), len(Bm))
    if n < 2:
        return float("nan")
    return float(np.corrcoef(A[:n].ravel(), Bm[:n].ravel())[0, 1])


# ---------------- configurable training (v7 math, tunable batch/epochs) ----
def train_model(model, X, Y, epochs, lr, batch, rng):
    n = len(X)
    for _ in range(epochs):
        idx = rng.permutation(n)
        for s in range(0, n, batch):
            bi = idx[s:s + batch]
            a = model.forward(X[bi])
            delta = 2 * (a[-1] - Y[bi]) * v7.LOSS_W / len(bi)
            for i in reversed(range(len(model.W))):
                gW = a[i].T @ delta
                gb = delta.sum(axis=0)
                if i > 0:
                    delta = (delta @ model.W[i].T) * (a[i] > 0)
                model.W[i] -= lr * gW
                model.b[i] -= lr * gb


# ---------------- corpus loading / encoding ----------------
def load_corpus():
    d = np.load(CORPUS, allow_pickle=True)
    inv = list(d["inv_phones"])
    PIDX = {p: i for i, p in enumerate(inv)}
    has_audio = "audios" in d.files
    utts = []
    for i in range(len(d["texts"])):
        F = d["Fs"][i].astype(float)
        phones = list(d["phones"][i])
        bounds = d["bounds"][i].astype(float)
        X, _ = v7.encode_frames(phones, bounds, len(F), PIDX)
        Y = v7.to_targets(F)
        au = d["audios"][i].astype(float) if has_audio else None
        utts.append(dict(hm=tuple(d["hm"][i]), text=str(d["texts"][i]),
                         X=X, Y=Y, F=F, audio=au))
    return utts, PIDX


# ---------------- one operating point: train, bake, evaluate ----------------
def evaluate_size(train_utts, test_utts, in_dim, epochs, lr, batch,
                  n_mel_eval, seed=0):
    Xtr = np.vstack([u["X"] for u in train_utts])
    Ytr = np.vstack([u["Y"] for u in train_utts])
    Xte = np.vstack([u["X"] for u in test_utts])
    Yte = np.vstack([u["Y"] for u in test_utts])

    rng = np.random.default_rng(seed)
    m = v7.Reg([in_dim, 64, 32, P + 3], rng)
    train_model(m, Xtr, Ytr, epochs, lr, batch, rng)
    ceil = [np.percentile(h, 99.5) for h in m.forward(Xtr)[1:-1]]

    pf = m.forward(Xte)[-1]
    rmse_f = np.sqrt(((pf - Yte) ** 2).mean(axis=0))

    chips = {}
    for name, s in [("A", 100), ("B", 200)]:
        Wn, b3 = v7.bake_chip(m, np.random.default_rng(s), Xtr, Ytr, ceil)
        out = v7.td_forward(m, Wn, Xte, v7.R_LEVELS,
                            np.random.default_rng(s + 1), ceil, b3)
        chips[name] = dict(Wn=Wn, b3=b3,
                           rmse=np.sqrt(((out - Yte) ** 2).mean(axis=0)))

    # spectrogram fidelity: chip-A resynthesis vs original audio, on a
    # deterministic subsample of test utterances that have cached audio
    corrs = []
    have = [u for u in test_utts if u["audio"] is not None]
    step = max(1, len(have) // max(1, n_mel_eval))
    WnA, b3A = chips["A"]["Wn"], chips["A"]["b3"]
    for u in have[::step][:n_mel_eval]:
        O = v7.td_forward(m, WnA, u["X"], v7.R_LEVELS,
                          np.random.default_rng(7), ceil, b3A)
        y_chip = v7.synth_lpc(v7.from_outputs(O))
        corrs.append(melspec_corr(u["audio"], y_chip))
    mel_corr_A = float(np.nanmean(corrs)) if corrs else float("nan")

    return dict(m=m, ceil=ceil, chips=chips, rmse_f=rmse_f,
                mel_corr_A=mel_corr_A, n_test_mel=len(corrs))


def render_demo(res, PIDX, in_dim):
    """At full corpus: demo wavs across the clock + viewer json (chip A)."""
    m, ceil = res["m"], res["ceil"]
    WnA, b3A = res["chips"]["A"]["Wn"], res["chips"]["A"]["b3"]
    d = np.load(CORPUS, allow_pickle=True)
    idx_by_hm = {tuple(d["hm"][i]): i for i in range(len(d["hm"]))}
    picks = [(3, 0), (3, 15), (3, 30), (3, 45), (10, 37), (12, 45)]
    os.makedirs("demo_audio", exist_ok=True)
    for (h, mm) in picks:
        i = idx_by_hm[(h, mm)]
        F = d["Fs"][i].astype(float)
        phones = list(d["phones"][i]); bounds = d["bounds"][i].astype(float)
        X, lab = v7.encode_frames(phones, bounds, len(F), PIDX)
        tag = f"{h:02d}{mm:02d}"
        # ceiling (true LPC) and chip A
        v7.write_wav(f"demo_audio/{tag}_ceiling.wav", v7.synth_lpc(F))
        O = v7.td_forward(m, WnA, X, v7.R_LEVELS,
                          np.random.default_rng(7), ceil, b3A)
        v7.write_wav(f"demo_audio/{tag}_chipA.wav",
                     v7.synth_lpc(v7.from_outputs(O)))
        if d.get("audios") is not None and "audios" in d.files:
            y = d["audios"][i].astype(float)
            v7.write_wav(f"demo_audio/{tag}_original.wav",
                         y / (np.abs(y).max() + 1e-9) * 0.85)
    print(f"  wrote demo_audio/ for {len(picks)} times")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="36,72,144,288,480,612,720")
    ap.add_argument("--epochs", type=int, default=250)
    ap.add_argument("--lr", type=float, default=0.06)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--mel-eval", type=int, default=24,
                    help="# test utterances for the melspec-corr metric")
    ap.add_argument("--test-frac", type=float, default=0.15)
    ap.add_argument("--quick", action="store_true",
                    help="tiny run: sizes 36,720, few epochs (pipeline check)")
    args = ap.parse_args()
    if args.quick:
        args.sizes, args.epochs = "36,720", 40

    t0 = time.time()
    utts, PIDX = load_corpus()
    in_dim = utts[0]["X"].shape[1]
    print(f"loaded {len(utts)} utterances, input dim {in_dim}, "
          f"{sum(len(u['F']) for u in utts)} frames  {time.time()-t0:.0f}s")

    # fixed utterance-level split
    order = np.random.default_rng(0).permutation(len(utts))
    n_test = int(round(args.test_frac * len(utts)))
    test_idx = set(order[:n_test].tolist())
    test_utts = [utts[i] for i in order[:n_test]]
    train_pool = [utts[i] for i in order[n_test:]]
    print(f"train pool {len(train_pool)}, test {len(test_utts)} "
          f"(fixed across all sizes)")

    sizes = [min(int(s), len(train_pool)) for s in args.sizes.split(",")]
    rows = []
    for sz in sizes:
        ts = time.time()
        res = evaluate_size(train_pool[:sz], test_utts, in_dim,
                            args.epochs, args.lr, args.batch, args.mel_eval)
        r = dict(
            corpus_size=sz,
            rmse_k_float=round(float(res["rmse_f"][:P].mean()), 4),
            rmse_k_chipA=round(float(res["chips"]["A"]["rmse"][:P].mean()), 4),
            rmse_k_chipB=round(float(res["chips"]["B"]["rmse"][:P].mean()), 4),
            rmse_F0_chipA=round(float(res["chips"]["A"]["rmse"][P]), 4),
            rmse_voice_chipA=round(float(res["chips"]["A"]["rmse"][P + 2]), 4),
            melcorr_chipA=round(res["mel_corr_A"], 4),
            n_test_mel=res["n_test_mel"],
            secs=round(time.time() - ts, 1),
        )
        rows.append(r)
        print(f"  size {sz:4d}: float k-RMSE {r['rmse_k_float']:.4f} | "
              f"chipA k-RMSE {r['rmse_k_chipA']:.4f} | "
              f"melcorr(chipA vs orig) {r['melcorr_chipA']:.4f}  "
              f"[{r['secs']:.0f}s]", flush=True)
        if sz == max(sizes):
            full = res

    with open("results_v13_scaling.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nsaved results_v13_scaling.csv  {time.time()-t0:.0f}s")

    render_demo(full, PIDX, in_dim)
    print(f"done  {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
