"""
build_corpus_v13.py — generate & cache the full 720-minute talking-clock
corpus (PB-2 / demo v13).

For every natural-time phrasing (time_phrases.all_times(), 720 utterances)
this runs the *validated v7 teacher/analysis path verbatim*:
    espeak-ng + MBROLA us1  -> 8 kHz speech + exact phoneme alignment
    LPC-10 analysis         -> per-frame [k1..k10, F0/300, gain, voicing]
and caches the result to corpus_v13.npz. The espeak/MBROLA + LPC pass is by
far the most expensive step (and the weak Ryzen 3 makes it slower), so we
cache it once; network training/scaling experiments then iterate on the
cache cheaply. Phone one-hot ENCODING is deliberately NOT cached here — it
depends on the global phone inventory and is cheap to redo at train time.

Requires the container (espeak-ng, mbrola, mbrola-us1, numpy, scipy). Run:
    python build_corpus_v13.py                 # full 720
    python build_corpus_v13.py --limit 20      # quick smoke test
    python build_corpus_v13.py --with-audio    # also cache raw 8k audio
Cache is skipped if corpus_v13.npz already exists (use --force to rebuild).

NOTE: imports tts_chip_sim_v7 (the verbatim v7 core, see PROVENANCE.md) only
to reuse phrase_audio_and_phones() and analyze(); it does not run v7's own
__main__.
"""
import argparse
import os
import time

import numpy as np

import time_phrases
import tts_chip_sim_v7 as v7

CACHE = "corpus_v13.npz"


def build_corpus(limit=None, with_audio=False):
    rows = list(time_phrases.all_times())
    if limit:
        rows = rows[:limit]
    n = len(rows)

    hm = np.zeros((n, 2), dtype=np.int16)
    texts = []
    Fs = np.empty(n, dtype=object)        # per-utterance LPC feature matrices
    phones = np.empty(n, dtype=object)    # per-utterance [(phone, dur_ms), ...]
    bounds = np.empty(n, dtype=object)    # per-utterance frame boundaries
    audios = np.empty(n, dtype=object) if with_audio else None
    inventory = {}

    t0 = time.time()
    total_frames = 0
    for i, (h, m, text) in enumerate(rows):
        y, ph = v7.phrase_audio_and_phones(text)
        F = v7.analyze(y)
        # frame->phone boundaries, exactly as v7.build() computes them
        b = np.cumsum([0] + [d for _, d in ph]) / 10.0
        for p, _ in ph:
            inventory.setdefault(p, len(inventory))
        hm[i] = (h, m)
        texts.append(text)
        Fs[i] = F.astype(np.float32)
        phones[i] = ph
        bounds[i] = b.astype(np.float32)
        if with_audio:
            audios[i] = y.astype(np.float32)
        total_frames += len(F)
        if i % 50 == 0 or i == n - 1:
            print(f"  [{i + 1:4d}/{n}] {text:34s} "
                  f"{len(F):3d} frames  {time.time() - t0:5.0f}s", flush=True)

    inventory.setdefault("_", len(inventory))   # padding phone, as in v7
    inv_phones = sorted(inventory, key=inventory.get)
    print(f"\ncorpus: {n} utterances, {len(inv_phones)} phones, "
          f"{total_frames} frames total, {time.time() - t0:.0f}s")
    return dict(hm=hm, texts=np.array(texts), Fs=Fs, phones=phones,
                bounds=bounds, inv_phones=np.array(inv_phones),
                audios=audios, with_audio=with_audio)


def save(cache, path=CACHE):
    payload = dict(hm=cache["hm"], texts=cache["texts"], Fs=cache["Fs"],
                   phones=cache["phones"], bounds=cache["bounds"],
                   inv_phones=cache["inv_phones"])
    if cache["with_audio"]:
        payload["audios"] = cache["audios"]
    np.savez_compressed(path, **payload)
    mb = os.path.getsize(path) / 1e6
    print(f"saved {path}  ({mb:.1f} MB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="only build the first N utterances (smoke test)")
    ap.add_argument("--with-audio", action="store_true",
                    help="also cache raw 8 kHz audio (bigger file)")
    ap.add_argument("--force", action="store_true",
                    help="rebuild even if the cache exists")
    args = ap.parse_args()

    out = CACHE if not args.limit else f"corpus_v13_first{args.limit}.npz"
    if os.path.exists(out) and not args.force:
        print(f"{out} exists; use --force to rebuild. Nothing to do.")
    else:
        cache = build_corpus(limit=args.limit, with_audio=args.with_audio)
        save(cache, out)
