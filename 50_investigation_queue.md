# 50_INVESTIGATION_QUEUE — consolidated & renumbered, 2026-07-25
*Priority-ordered. Items retired this session: nodal IR solve (v12), MNIST-scale cliff check partially covered by v8 architecture sweep.*

## P0 — validity & cross-checks
1. **AIHWKit CRN port**: order factor + 15–20 seeds on analog tiles; the last big cross-validation gap (all v4–v12 numpy-side).
2. **F2 autopsy**: loss traces on the AIHWKit 94.6% config; keep/delete variance-first.
3. **Modality dropout on the sum bus** (prerequisite for trusting F14 flat-power end-to-end): absent-modality operating-point shift; per-modality "present" bias line if needed.
4. Vary train/test split per seed (honest absolute CIs) alongside fixed-split paired arm.

## P1 — the paper's load-bearing extensions
5. Inverted-multimodal test: PARTIALLY BAKED encoders → where the dormant core adapter earns its keep; scale core & novelty of post-fab joint function to find where frozen-core re-purposing breaks; >2 heads.
6. Overparameterization control for F9 (harder task / matched capacity) before claiming "bigger bakes better" generally.
7. Encoding × frozen-ratio 2D DSE (extends claimed gap; nobody has crossed these axes).
8. Leakage-aware cost function folded into the v4 Pareto (does the sweet spot shift?).
9. Per-layer independent R sweep (output likely needs more than L1 → shave latency further).
10. Vocabulary-size knob on the F7 output-only-recovery proviso.
11. F6 energy per baking order (does reverse-order chaining match forward?).

## P2 — hardware realism
12. Better IR compensation solver (damped/global); memristor I-V nonlinearity in the nodal model; real regulator model for rail droop.
13. SPICE (NGSpice) one printed L1 column vs behavioral model; RC + OTS/NbO2 relaxation neuron spec & SPICE; shadow-mask pitch study for the 32×13 head vs sputter-coater feature size.
14. RC temporal basis follow-ups: τ bank sweep; RC delay-line long context; CR delta channels; printed-cap tolerance in the noise model; bigger vocabulary test of the F12b ">" (anticipatory coarticulation).
15. Write-limited fine-tune (endurance realism); NeuroSim conventions replacing hand cost proxy.
16. v7 voicing channel: derive deterministically from phone identity in control plane.
17. Drift-over-weeks audio with real AIHWKit PCM model (the killer demo take).

## P3 — queued by Avery, do not start
18. **Memristor transformer**: baked W_Q/K/V/O + FFN (>90% params — frozen-ratio transfers), attention product via time-domain analog multiplier or control plane; linear-attention variants map better (fixed feature maps bakeable, state = accumulating outer product / capacitor bank); literature check first (X-Former, TranCIM etc. own attention-in-crossbar; the hybrid/frozen angle is ours).

## Paper skeleton note
The thesis is now the design law (30_design_rules). Suggested structure: frozen-ratio DSE (F1/F7/F8/F9) → encoding & system (F10/F13) → calibration & robustness (F11/F15/F5) → multimodal topology (F14) → PB-1 demonstrator (F12) → honest limitations ledger.
