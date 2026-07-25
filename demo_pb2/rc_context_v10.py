"""
rc_context_v10.py — baked RC networks as temporal computation.

Idea: replace the v7 input's prev/next phone context (which needs lookahead
and 3x the lines) with RC low-pass filtered copies of the CURRENT phone
one-hot. A printed R + printed C on each line is a leaky integrator; a bank
of time constants is a temporal basis, fully baked, zero transistors:

  v7 baseline : [prev 25 | cur 25 | next 25 | pos 5] = 80 lines, needs
                phoneme lookahead (non-causal)
  RC variant  : [cur 25 | RC tau=30ms 25 | RC tau=100ms 25] = 75 lines,
                strictly causal (streaming), position info implicit in the
                RC charge state.

Same training, baking, per-chip head calibration, TD eval as v7.
"""
import numpy as np, time
import tts_chip_sim_v7 as v7

def rc_filter(X, tau_ms, frame_ms=10):
    a = np.exp(-frame_ms / tau_ms)
    Y = np.zeros_like(X)
    acc = np.zeros(X.shape[1])
    for t in range(len(X)):
        acc = a * acc + (1 - a) * X[t]
        Y[t] = acc
    return Y

def encode_rc(phones, bounds, n_fr, PIDX):
    NPh = len(PIDX)
    seq = [p for p, dur in phones]
    cur = np.zeros((n_fr, NPh))
    for f in range(n_fr):
        k = max(0, min(np.searchsorted(bounds, f + 0.5) - 1, len(seq) - 1))
        cur[f, PIDX[seq[k]]] = 1
    return np.hstack([cur, rc_filter(cur, 30), rc_filter(cur, 100)])

if __name__ == "__main__":
    t0 = time.time()
    data, PIDX = v7.build()
    PIDX.setdefault("_", len(PIDX))
    test_keys = {("three","thirty"), ("seven","fifteen"), ("twelve","o'clock"),
                 ("five","thirty"), ("nine","o'clock"), ("one","fifteen")}
    Xtr, Ytr, Xte, Yte = [], [], [], []
    demo = None
    for (h, m_, y, F, phones, bounds) in data:
        X = encode_rc(phones, bounds, len(F), PIDX)
        Y = v7.to_targets(F)
        (Xte if (h, m_) in test_keys else Xtr).append(X)
        (Yte if (h, m_) in test_keys else Ytr).append(Y)
        if (h, m_) == ("three", "thirty"):
            demo = (X, F)
    Xtr, Ytr = np.vstack(Xtr), np.vstack(Ytr)
    Xte, Yte = np.vstack(Xte), np.vstack(Yte)
    print("inputs:", Xtr.shape[1], "(v7 baseline: 80)")

    rng = np.random.default_rng(0)
    m = v7.Reg([Xtr.shape[1], 64, 32, v7.P + 3], rng)
    m.train(Xtr, Ytr, 500, 0.06, rng)
    ceil = [np.percentile(h, 99.5) for h in m.forward(Xtr)[1:-1]]
    pf = m.forward(Xte)[-1]
    r = np.sqrt(((pf - Yte) ** 2).mean(axis=0))
    print(f"RC-causal float RMSE: k:{r[:10].mean():.4f} F0:{r[10]:.4f} "
          f"g:{r[11]:.4f} v:{r[12]:.4f}")
    print("v7 baseline float was: k:0.0615 F0:0.0486 g:0.0525 v:0.1831")

    Wn, b3 = v7.bake_chip(m, np.random.default_rng(100), Xtr, Ytr, ceil)
    out = v7.td_forward(m, Wn, Xte, v7.R_LEVELS, np.random.default_rng(101), ceil, b3)
    rc = np.sqrt(((out - Yte) ** 2).mean(axis=0))
    print(f"RC-causal chip  RMSE: k:{rc[:10].mean():.4f} F0:{rc[10]:.4f} "
          f"g:{rc[11]:.4f} v:{rc[12]:.4f}")
    print("v7 baseline chipA was: k:0.0865 F0:0.0792 g:0.0923 v:0.1924")

    Xd, Fd = demo
    O = v7.td_forward(m, Wn, Xd, v7.R_LEVELS, np.random.default_rng(102), ceil, b3)
    v7.write_wav("v10_chip_RC_causal.wav", v7.synth_lpc(v7.from_outputs(O)))
    print(f"wav saved  {time.time()-t0:.0f}s")
