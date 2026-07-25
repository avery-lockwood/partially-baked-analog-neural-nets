# What's next

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
