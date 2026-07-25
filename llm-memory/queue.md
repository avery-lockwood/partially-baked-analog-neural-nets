# What's next

## ACTIVE WORKSTREAM (set 2026-07-25): scaled demo + paper
Avery's current priority — see `60_demo_and_paper_goals.md` in the project
root for the full spec. Ordered:
1. Get the Docker container (`analog-nn-dev`) reachable — blocked on
   `sudo usermod -aG docker avery` + shell group refresh (see
   environment.md). All heavy runs go through the container.
2. Scale the talking-clock corpus 36 → full natural-time space (~720
   utterances, natural phrasings). Cache analyzed LPC frames to .npz so
   network iteration is cheap (corpus gen is the expensive part on the weak
   Ryzen 3).
3. Retrain the baked core on the large corpus; measure spectrogram fidelity
   vs. corpus size — this scaling curve is the headline paper figure (does
   the fixed baked core generalize or saturate?).
4. RC-causal streaming front end (v10 path) on the large corpus.
5. New interactive web viewer (clock face + charge flow + audio) for the
   website, extending build_viewer.py / chip_viewer.html.
6. `70_literature_validation.md`: map each sim assumption (5% fab noise, 16
   write levels, drift, IR) and each headline result to a citable number
   from published analog-IMC / memristor / printed-electronics / LPC
   literature, stating honestly where our numbers are optimistic. This is
   the paper's "validation citing other papers" requirement.

The v4-v12 investigation queue below is still valid but now secondary to the
demo/paper push unless Avery redirects.

---

Condensed from `50_investigation_queue.md` — check that file for full detail
before starting anything; this is a priority-ordered pointer, not the full
spec.

## P0 — validity & cross-checks (do these first)
1. AIHWKit CRN port — last big cross-validation gap (all v4-v12 work is
   numpy-side only).
2. F2 autopsy — loss traces on the AIHWKit 94.6% config; decide keep/delete
   on variance-first.
3. Modality dropout on the sum bus — prerequisite for trusting F14's
   flat-power claim end to end.
4. Vary train/test split per seed for honest absolute CIs.

## P1 — the paper's load-bearing extensions
5. Inverted-multimodal test (partially-baked encoders).
6. Overparameterization control for F9 before claiming "bigger bakes
   better" generally.
7. Encoding × frozen-ratio 2D DSE.
8. Leakage-aware cost function in the Pareto.
9. Per-layer independent R sweep.
10. Vocabulary-size knob on the F7 output-only-recovery proviso.
11. F6 energy per baking order.

## P2 — hardware realism
12-17. Better IR compensation solver, memristor I-V nonlinearity, SPICE
validation, RC temporal-basis follow-ups, write-limited fine-tune realism,
drift-over-weeks with real AIHWKit PCM model.

## P3 — queued by Avery, do NOT start unprompted
18. Memristor transformer (baked W_Q/K/V/O + FFN). Explicitly deferred —
    respect this, don't pick it up without her asking.

## Paper skeleton (from 50_investigation_queue.md)
Frozen-ratio DSE (F1/F7/F8/F9) → encoding & system (F10/F13) →
calibration & robustness (F11/F15/F5) → multimodal topology (F14) → PB-1
demonstrator (F12) → honest limitations ledger.
