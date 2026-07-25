"""
tts_chip_sim_v7.py — intelligible talking-clock chip.

Upgrade over v6: the teacher is now REAL SPEECH (espeak-ng + MBROLA us1
diphone voice), and the chip's output representation is LPC-10:
10 reflection coefficients + F0 + gain + voicing per 10 ms frame — the
exact representation of the TI TMS5100 in the 1978 Speak & Spell, which is
the project's stated design heritage. Reflection coefficients are bounded
[-1,1] and precision-tolerant (the filter is stable for any |k|<1), which
is why LPC vocoders survived 4-6 bit quantization in the 70s — and why
they survive analog noise now.

Pipeline per phrase:
  espeak --pho  -> exact phoneme sequence + per-phone durations (alignment)
  espeak+mbrola -> 16 kHz speech, resampled to 8 kHz
  LPC-10 analysis (25 ms window / 10 ms hop, Levinson-Durbin) -> targets
  chip: one-hot phone-context binary input -> baked L1+L2 -> memristor L3
        -> 13 analog pulse widths -> all-pole resynthesis.

Voices out: mbrola original / LPC vocoder ceiling / chip A / chip B /
chip A drifted head.
"""
import numpy as np, subprocess, wave, struct, json, time, os
from scipy.signal import resample_poly

FS = 8000
HOP = 80                # 10 ms
WIN = 200               # 25 ms
P = 10                  # LPC order
SIGMA_FAB, SIGMA_PROG, N_LEVELS, R_LEVELS = 0.05, 0.04, 16, 32
rng_global = np.random.default_rng
LOSS_W = np.array([1.0]*10 + [3.0, 2.0, 3.0])

HOURS = ["one","two","three","four","five","six","seven","eight","nine",
         "ten","eleven","twelve"]
MINS = ["o'clock","thirty","fifteen"]
VOICE = "us-mbrola-1"

# ---------------- espeak/mbrola frontend ----------------
def phrase_audio_and_phones(text):
    subprocess.run(["espeak-ng","-v",VOICE,"-s","140","-w","_tmp.wav",text],
                   check=True, capture_output=True)
    pho = subprocess.run(["espeak-ng","-v",VOICE,"-s","140","--pho","-q",text],
                         check=True, capture_output=True, text=True).stdout
    phones = []
    for line in pho.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 2:
            phones.append((parts[0], int(parts[1])))
    w = wave.open("_tmp.wav"); sr = w.getframerate()
    y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16) / 32768.0
    w.close()
    y = resample_poly(y, FS, sr)
    return y, phones

# ---------------- LPC analysis ----------------
def levinson(rx):
    a = np.zeros(P + 1); a[0] = 1.0; e = rx[0]; k = np.zeros(P)
    for i in range(1, P + 1):
        acc = rx[i] + np.dot(a[1:i], rx[i - 1:0:-1])
        ki = -acc / (e + 1e-12); k[i - 1] = ki
        a[1:i] = a[1:i] + ki * a[i - 1:0:-1]
        a[i] = ki; e *= (1 - ki * ki)
    return a, k, max(e, 1e-9)

def analyze(y):
    n_fr = max(0, (len(y) - WIN) // HOP + 1)
    feats = np.zeros((n_fr, P + 3))          # k1..k10, F0/300, gain, voicing
    win = np.hamming(WIN)
    for f in range(n_fr):
        s = y[f * HOP:f * HOP + WIN] * win
        s = s - s.mean()
        rx = np.correlate(s, s, "full")[WIN - 1:WIN + P]
        if rx[0] < 1e-7:
            continue
        a, k, e = levinson(rx)
        # F0 via autocorrelation peak 60-320 Hz
        r_full = np.correlate(s, s, "full")[WIN - 1:]
        lo, hi = FS // 320, FS // 60
        seg = r_full[lo:hi]
        pk = np.argmax(seg) + lo
        voiced = 1.0 if r_full[pk] / (r_full[0] + 1e-12) > 0.30 else 0.0
        f0 = FS / pk if voiced else 0.0
        feats[f, :P] = np.clip(k, -0.98, 0.98)
        feats[f, P] = f0 / 300.0
        feats[f, P + 1] = np.sqrt(e)
        feats[f, P + 2] = voiced
    feats[:, P + 1] /= (feats[:, P + 1].max() + 1e-9)   # per-phrase gain norm
    # continuous F0 target: interpolate through unvoiced spans (voicing
    # channel does the gating; regression target stays smooth)
    f0 = feats[:, P]; v = feats[:, P + 2] > 0.5
    if v.any():
        idx = np.arange(len(f0))
        feats[:, P] = np.interp(idx, idx[v], f0[v])
        med = np.copy(feats[:, P])
        for i in range(1, len(med) - 1):
            feats[i, P] = np.median(med[i - 1:i + 2])
    return feats

# ---------------- dataset ----------------
def build():
    data = []
    inventory = {}
    for h in HOURS:
        for m in MINS:
            text = f"it is {h} {m}"
            y, phones = phrase_audio_and_phones(text)
            F = analyze(y)
            # frame -> phone alignment from exact durations
            seq = [p for p, d in phones]
            for p in seq:
                inventory.setdefault(p, len(inventory))
            bounds = np.cumsum([0] + [d for _, d in phones]) / 10.0  # frames
            data.append((h, m, y, F, phones, bounds))
    return data, inventory

def encode_frames(phones, bounds, n_fr, PIDX):
    NPh = len(PIDX)
    seq = [p for p, d in phones]
    X = np.zeros((n_fr, 3 * NPh + 5))
    lab = []
    for f in range(n_fr):
        k = min(np.searchsorted(bounds, f + 0.5) - 1, len(seq) - 1)
        k = max(k, 0)
        prev = seq[k - 1] if k > 0 else "_"
        nxt = seq[k + 1] if k < len(seq) - 1 else "_"
        span = max(bounds[k + 1] - bounds[k], 1)
        pos = min(4, int(5 * (f - bounds[k]) / span))
        X[f, PIDX[prev]] = 1
        X[f, NPh + PIDX[seq[k]]] = 1
        X[f, 2 * NPh + PIDX[nxt]] = 1
        X[f, 3 * NPh:3 * NPh + pos + 1] = 1
        lab.append(seq[k])
    return X, lab

# ---------------- model (as v6) ----------------
relu = lambda x: np.maximum(0, x)
class Reg:
    def __init__(self, sizes, rng):
        self.sizes = sizes
        self.W = [rng.normal(0, np.sqrt(2 / sizes[i]), (sizes[i], sizes[i + 1]))
                  for i in range(len(sizes) - 1)]
        self.b = [np.zeros(sizes[i + 1]) for i in range(len(sizes) - 1)]
    def forward(self, X):
        a = [X]
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            z = a[-1] @ W + b
            a.append(relu(z) if i < len(self.W) - 1 else z)
        return a
    def train(self, X, Y, epochs, lr, rng):
        n = len(X)
        for ep in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, 64):
                bi = idx[s:s + 64]
                a = self.forward(X[bi])
                delta = 2 * (a[-1] - Y[bi]) * LOSS_W / len(bi)
                for i in reversed(range(len(self.W))):
                    gW = a[i].T @ delta; gb = delta.sum(axis=0)
                    if i > 0:
                        delta = (delta @ self.W[i].T) * (a[i] > 0)
                    self.W[i] -= lr * gW; self.b[i] -= lr * gb

def bake_chip(model, rng, Xcal=None, Ycal=None, ceil=None):
    Wn = [model.W[0] * (1 + rng.normal(0, SIGMA_FAB, model.W[0].shape)),
          model.W[1] * (1 + rng.normal(0, SIGMA_FAB, model.W[1].shape))]
    W3 = model.W[2]; b3 = model.b[2]
    if Xcal is not None:
        # measure THIS chip's baked activations (with TD read noise) and
        # ridge-solve the programmable head = write-verify calibration
        a = Xcal
        for i in range(2):
            z = a @ Wn[i] + model.b[i]
            a = np.clip(relu(z) + rng.normal(0, ceil[i]/R_LEVELS, z.shape),
                        0, ceil[i])
        A = np.hstack([a, np.ones((len(a), 1))])
        lam = 1e-3 * len(A)
        M = np.linalg.solve(A.T @ A + lam*np.eye(A.shape[1]), A.T @ Ycal)
        W3, b3 = M[:-1], M[-1]
    s = np.abs(W3).max() + 1e-12
    step = 1.0 / (N_LEVELS - 1)
    q = lambda G: np.clip(np.round(G / step) * step
                          + rng.normal(0, SIGMA_PROG, G.shape), 0, 1)
    Wn.append((q(np.clip(W3, 0, None) / s) - q(np.clip(-W3, 0, None) / s)) * s)
    return Wn, b3

def td_forward(model, Wn, X, R, rng, ceil, b3=None, R_out=64):
    bs = [model.b[0], model.b[1], b3 if b3 is not None else model.b[2]]
    a = X.copy()
    for i, (W, b) in enumerate(zip(Wn, bs)):
        z = a @ W + b
        if i < len(Wn) - 1:
            a = np.clip(relu(z) + rng.normal(0, ceil[i] / R, z.shape), 0, ceil[i])
        else:
            out = np.clip(relu(z) + rng.normal(0, 1.0 / R_out, z.shape), 0, 1.05)
    return out

# outputs are shifted to [0,1]: k' = (k+1)/2. Undo at synthesis.
def to_targets(F):
    Y = F.copy(); Y[:, :P] = (Y[:, :P] + 1) / 2; return Y
def from_outputs(O):
    F = O.copy(); F[:, :P] = np.clip(F[:, :P] * 2 - 1, -0.97, 0.97); return F

# ---------------- LPC synthesis ----------------
def k_to_a(k):
    a = np.zeros(P + 1); a[0] = 1.0
    for i in range(1, P + 1):
        prev = a[1:i].copy()
        a[1:i] = prev + k[i - 1] * prev[::-1]
        a[i] = k[i - 1]
    return a

def synth_lpc(F, smooth=True):
    F = F.copy()
    v = (F[:, P + 2] > 0.5).astype(float)
    for i in range(1, len(v) - 1):                 # 3-frame median: no flicker
        F[i, P + 2] = np.median(v[i - 1:i + 2])
    F[:, P + 1] = np.clip(F[:, P + 1], 0, 1.0)
    if smooth:
        for c in range(F.shape[1]):
            F[1:-1, c] = 0.25 * F[:-2, c] + 0.5 * F[1:-1, c] + 0.25 * F[2:, c]
    n = len(F) * HOP
    y = np.zeros(n + P); rng = rng_global(3)
    phase = 0.0
    for f in range(len(F)):
        k = F[f, :P]; f0 = F[f, P] * 300; g = F[f, P + 1]; v = F[f, P + 2]
        a = k_to_a(k)
        voiced = v > 0.5 and f0 > 55
        for s in range(HOP):
            i = f * HOP + s + P
            if voiced:
                phase += f0 / FS
                exc = 0.0
                if phase >= 1.0:
                    phase -= 1.0; exc = 1.0
                exc *= np.sqrt(FS / max(f0, 1))
            else:
                exc = rng.normal(0, 0.55)
            y[i] = g * exc - np.dot(a[1:], y[i - P:i][::-1])
    y = y[P:]
    return y / (np.abs(y).max() + 1e-9) * 0.85

def write_wav(path, y):
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(FS)
        w.writeframes(struct.pack("<%dh" % len(y),
                                  *(np.clip(y, -1, 1) * 32767).astype(np.int16)))

# ---------------- run ----------------
if __name__ == "__main__":
    t0 = time.time()
    data, PIDX = build()
    PIDX.setdefault("_", len(PIDX))
    NPh = len(PIDX)
    print(f"corpus: {len(data)} phrases, {NPh} phones, "
          f"{sum(len(d[3]) for d in data)} frames  {time.time()-t0:.0f}s")
    test_keys = {("three","thirty"), ("seven","fifteen"), ("twelve","o'clock"),
                 ("five","thirty"), ("nine","o'clock"), ("one","fifteen")}
    Xtr, Ytr, Xte, Yte = [], [], [], []
    demo = None
    for (h, m, y, F, phones, bounds) in data:
        X, lab = encode_frames(phones, bounds, len(F), PIDX)
        Y = to_targets(F)
        if (h, m) in test_keys:
            Xte.append(X); Yte.append(Y)
        else:
            Xtr.append(X); Ytr.append(Y)
        if (h, m) == ("three", "thirty"):
            demo = (X, F, lab, y)
    Xtr, Ytr = np.vstack(Xtr), np.vstack(Ytr)
    Xte, Yte = np.vstack(Xte), np.vstack(Yte)
    print("train", Xtr.shape, "test", Xte.shape)

    rng = rng_global(0)
    m = Reg([Xtr.shape[1], 64, 32, P + 3], rng)
    m.train(Xtr, Ytr, 500, 0.06, rng)
    ceil = [np.percentile(h, 99.5) for h in m.forward(Xtr)[1:-1]]
    pf = m.forward(Xte)[-1]
    rmse_f = np.sqrt(((pf - Yte) ** 2).mean(axis=0))

    chips = {}
    for name, seed in [("A", 100), ("B", 200)]:
        Wn, b3 = bake_chip(m, rng_global(seed), Xtr, Ytr, ceil)
        out = td_forward(m, Wn, Xte, R_LEVELS, rng_global(seed + 1), ceil, b3)
        chips[name] = (Wn, np.sqrt(((out - Yte) ** 2).mean(axis=0)), b3)
    print("\nRMSE (normalized): mean over k1-k10 | F0 | gain | voicing")
    for tag, r in [("float", rmse_f), ("chipA", chips["A"][1]),
                   ("chipB", chips["B"][1])]:
        print(f"  {tag:6s} k:{r[:P].mean():.4f}  F0:{r[P]:.4f} "
              f"({r[P]*300:.1f} Hz)  g:{r[P+1]:.4f}  v:{r[P+2]:.4f}")

    # ---- audio: demo phrase ----
    Xd, Fd, lab, y_orig = demo
    write_wav("v7_mbrola_original.wav", y_orig / (np.abs(y_orig).max() + 1e-9) * 0.85)
    write_wav("v7_vocoder_ceiling.wav", synth_lpc(Fd))
    for name, seed in [("A", 100), ("B", 200)]:
        Wn, _, b3 = chips[name]
        O = td_forward(m, Wn, Xd, R_LEVELS, rng_global(seed + 2), ceil, b3)
        write_wav(f"v7_chip_{name}.wav", synth_lpc(from_outputs(O)))
    Wd = [w.copy() for w in chips["A"][0]]
    Wd[2] = Wd[2] * 0.65 + 0.35 * np.sign(Wd[2]) * np.abs(Wd[2]).mean()
    O = td_forward(m, Wd, Xd, R_LEVELS, rng_global(999), ceil, chips["A"][2])
    write_wav("v7_chip_A_drifted.wav", synth_lpc(from_outputs(O)))

    # ---- viz export (same schema as v6 viewer) ----
    Wn = chips["A"][0]; b3A = chips["A"][2]
    acts = []; aa = Xd; r2 = rng_global(102)
    for i, (W, b) in enumerate(zip(Wn, [m.b[0], m.b[1], b3A])):
        z = aa @ W + b
        aa = (np.clip(relu(z) + r2.normal(0, ceil[i] / R_LEVELS, z.shape), 0, ceil[i])
              if i < 2 else np.clip(relu(z), 0, 1.05))
        acts.append(aa)
    pn = [f"k{i+1}" for i in range(P)] + ["F0", "gain", "voice"]
    viz = dict(phrase="it is three thirty", phones=lab,
        input_dim=int(Xd.shape[1]), n_phones=NPh,
        layers=[dict(name=f"L1 baked {Xd.shape[1]}x64", rows=int(Xd.shape[1]),
                     cols=64, W=np.round(Wn[0], 3).tolist(), baked=True),
                dict(name="L2 baked 64x32", rows=64, cols=32,
                     W=np.round(Wn[1], 3).tolist(), baked=True),
                dict(name=f"L3 memristor 32x{P+3}", rows=32, cols=P + 3,
                     W=np.round(Wn[2], 3).tolist(), baked=False)],
        ceilings=[float(c) for c in ceil] + [1.05],
        frames=dict(input=[np.flatnonzero(Xd[i]).tolist() for i in range(len(Xd))],
                    a1=np.round(acts[0], 3).tolist(),
                    a2=np.round(acts[1], 3).tolist(),
                    out=np.round(acts[2], 3).tolist()),
        scale=[1.0] * P + [300.0, 1.0, 1.0], param_names=pn, frame_ms=10)
    json.dump(viz, open("viz_data.json", "w"))
    n_w = sum(np.prod(w.shape) for w in Wn)
    print(f"\nweights: {n_w} ({int(Wn[2].size)} programmable = "
          f"{Wn[2].size/n_w*100:.1f}%)  saved wavs+viz  {time.time()-t0:.0f}s")
