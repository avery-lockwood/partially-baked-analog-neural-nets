"""
build_demo_v13.py — emit data + audio for the PB-2 interactive clock viewer.

Trains the full-corpus baked chip once (baked L1/L2 + per-chip calibrated
memristor head), then for a curated showcase set of times that exercises
every natural phrasing type (o'clock / N past / quarter past / half past /
quarter to / N to, incl. the 12->1 wrap) it emits:
  - demo_v13_data.json : baked weights ONCE (shared across all times) +
    per-utterance phone track and per-frame activations (input/a1/a2/out)
  - demo_audio/<HHMM>_{chipA,ceiling,original}.wav

The weights are identical for every utterance (one physical chip), so only
the activations/audio vary per time — keeps the embedded demo compact.
build_clock_viewer.py turns these into a single self-contained HTML page.

Run in the container:
    python build_demo_v13.py --epochs 250
"""
import argparse
import base64
import json
import os
import time

import numpy as np

import tts_chip_sim_v7 as v7
import drift_v13 as dr
from train_scale_v13 import load_corpus, train_model, P

DRIFT_WEEKS = [4, 8, 12]   # pre-rendered aged-audio points for the week slider

# showcase times: one per phrasing type, spread around the clock face
SHOWCASE = [
    (12, 0), (3, 0), (9, 0),          # o'clock
    (1, 10), (5, 5), (6, 25),         # N past
    (2, 15), (9, 15),                 # quarter past
    (3, 30), (10, 30),                # half past
    (4, 45), (11, 45), (12, 45),      # quarter to (12:45 -> "one")
    (7, 40), (8, 50), (6, 55),        # N to
]


def chip_activations(m, Wn, ceil, X, b3):
    """Per-frame activations through the baked+calibrated chip (chip A),
    matching the viz export in tts_chip_sim_v7.py."""
    acts = []
    a = X.copy()
    r = np.random.default_rng(102)
    for i, (W, b) in enumerate(zip(Wn, [m.b[0], m.b[1], b3])):
        z = a @ W + b
        if i < 2:
            a = np.clip(v7.relu(z) + r.normal(0, ceil[i] / v7.R_LEVELS, z.shape),
                        0, ceil[i])
        else:
            a = np.clip(v7.relu(z), 0, 1.05)
        acts.append(a)
    return acts  # [a1 (64), a2 (32), out (13)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=250)
    ap.add_argument("--lr", type=float, default=0.06)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--test-frac", type=float, default=0.15)
    args = ap.parse_args()

    t0 = time.time()
    utts, PIDX = load_corpus()
    in_dim = utts[0]["X"].shape[1]
    by_hm = {u["hm"]: u for u in utts}
    print(f"loaded {len(utts)} utts, in_dim {in_dim}  {time.time()-t0:.0f}s")

    # same fixed split + training as the scaling experiment's full point
    order = np.random.default_rng(0).permutation(len(utts))
    n_test = int(round(args.test_frac * len(utts)))
    train_pool = [utts[i] for i in order[n_test:]]
    Xtr = np.vstack([u["X"] for u in train_pool])
    Ytr = np.vstack([u["Y"] for u in train_pool])

    rng = np.random.default_rng(0)
    m = v7.Reg([in_dim, 64, 32, P + 3], rng)
    train_model(m, Xtr, Ytr, args.epochs, args.lr, args.batch, rng)
    ceil = [np.percentile(h, 99.5) for h in m.forward(Xtr)[1:-1]]
    # expose the head's differential conductances so it can be drifted (the
    # week-0 net head is identical to v7.bake_chip's)
    Wn12, Gp, Gn, s, b3 = dr.bake_head_full(m, np.random.default_rng(100),
                                            Xtr, Ytr, ceil)
    Wn = Wn12 + [(Gp - Gn) * s]
    nrng = np.random.default_rng(77)   # ONE fixed per-device drift draw; JS reuses it
    nup = np.clip(0.06 + 0.012 * nrng.standard_normal(Gp.shape), 0, None)
    nun = np.clip(0.06 + 0.012 * nrng.standard_normal(Gn.shape), 0, None)
    print(f"trained + baked chip A  {time.time()-t0:.0f}s")

    os.makedirs("demo_audio", exist_ok=True)
    param_names = [f"k{i+1}" for i in range(P)] + ["F0", "gain", "voice"]
    data = dict(
        layers=[
            dict(name=f"L1 baked {in_dim}x64", rows=in_dim, cols=64,
                 W=np.round(Wn[0], 3).tolist(), baked=True),
            dict(name="L2 baked 64x32", rows=64, cols=32,
                 W=np.round(Wn[1], 3).tolist(), baked=True),
            dict(name=f"L3 memristor 32x{P+3}", rows=32, cols=P + 3,
                 W=np.round(Wn[2], 3).tolist(), baked=False),
        ],
        ceilings=[float(c) for c in ceil] + [1.05],
        scale=[1.0] * P + [300.0, 1.0, 1.0],
        param_names=param_names, frame_ms=10, in_dim=in_dim,
        # everything the browser needs to age the memristor head live (baked
        # core L1/L2 is immune, so a1/a2 never change — only the head drifts)
        head=dict(Gp=np.round(Gp, 4).tolist(), Gn=np.round(Gn, 4).tolist(),
                  nup=np.round(nup, 4).tolist(), nun=np.round(nun, 4).tolist(),
                  scale=float(s), b3=np.round(b3, 4).tolist(),
                  t0_weeks=dr.T0_WEEKS, out_clip=1.05),
        drift_weeks=DRIFT_WEEKS, drift_max=12,
        utterances=[],
    )

    # phone track + frame boundaries live in the corpus cache; index them once
    d = np.load("corpus_v13.npz", allow_pickle=True)
    idx_by_hm = {tuple(d["hm"][i]): i for i in range(len(d["hm"]))}

    for (h, mm) in SHOWCASE:
        u = by_hm[(h, mm)]
        i = idx_by_hm[(h, mm)]
        F = u["F"]
        phones = list(d["phones"][i])
        bounds = d["bounds"][i].astype(float)
        X, lab = v7.encode_frames(phones, bounds, len(F), PIDX)
        a1, a2, out = chip_activations(m, Wn, ceil, X, b3)

        tag = f"{h:02d}{mm:02d}"
        O = v7.td_forward(m, Wn, X, v7.R_LEVELS, np.random.default_rng(7), ceil, b3)
        v7.write_wav(f"demo_audio/{tag}_chipA.wav", v7.synth_lpc(v7.from_outputs(O)))
        # software-ideal: the trained network with no analog noise (isolates the
        # analog-hardware penalty = the chipA-vs-float gap)
        Of = m.forward(X)[-1]
        v7.write_wav(f"demo_audio/{tag}_float.wav", v7.synth_lpc(v7.from_outputs(Of)))
        v7.write_wav(f"demo_audio/{tag}_ceiling.wav", v7.synth_lpc(F))
        # aged-head audio for the week slider (uncompensated drift)
        for wk in DRIFT_WEEKS:
            W3w = dr.drift_head_nu(Gp, Gn, s, wk, nup, nun)
            Ow = v7.td_forward(m, Wn12 + [W3w], X, v7.R_LEVELS,
                               np.random.default_rng(7), ceil, b3)
            v7.write_wav(f"demo_audio/{tag}_drift{wk}.wav",
                         v7.synth_lpc(v7.from_outputs(Ow)))
        if u["audio"] is not None:
            y = u["audio"]
            v7.write_wav(f"demo_audio/{tag}_original.wav",
                         y / (np.abs(y).max() + 1e-9) * 0.85)

        data["utterances"].append(dict(
            h=h, m=mm, tag=tag, text=u["text"], phones=lab,
            frames=dict(
                input=[np.flatnonzero(X[f]).tolist() for f in range(len(X))],
                a1=np.round(a1, 3).tolist(),
                a2=np.round(a2, 3).tolist(),
                out=np.round(out, 3).tolist()),
        ))
        print(f"  {tag} {u['text']:28s} {len(F):3d} frames")

    json.dump(data, open("demo_v13_data.json", "w"))
    sz = os.path.getsize("demo_v13_data.json") / 1e6
    print(f"\nsaved demo_v13_data.json ({sz:.1f} MB), "
          f"{len(SHOWCASE)} showcase times  {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
