# 10_FINDINGS_v2 — full results, v4–v12 session (2026-07-25)
*Keywords: CRN, baking order, cliff, boundary, scaling, time-domain, PWM, one-hot, first-spike, head calibration, LPC-10, drift audio, power, leakage, multimodal, interference, sum bus, RC, nodal, IR, compensation, clipping, rail droop*

## Common protocol upgrades (v4, apply everywhere after)
- **Common random numbers (CRN):** every (seed, condition) draws device/fine-tune noise from a SeedSequence keyed on (seed, condition-invariant index), so contrasted conditions see identical noise. Tightened IR contrasts 10–20×; exposed a spurious v1 result (−2.70pp at p=0.004 for the *mildest* IR setting — methodological artifact, gone under CRN).
- 30 seeds for the core ratio study (was 5); paired per-seed tests; McNemar on per-sample correctness vectors (post_vectors_v4.npz) for within-test-set contrasts (resolved 90% vs 94.6% at p=2e-5 where across-seed could not).
- Power note: paired sd between adjacent ratios ≈4.5pp at n=5 → v1 could only resolve ≥5pp effects; every "plateau wiggle" was noise floor.

## F1 (revised) — no plateau; linear decline + boundary knee
Forward order, digits 64-48-24-10: acc_shift_post declines **−1.03pp per 10% frozen** across 0–90% (t=−15.2, p=2.3e-15, 30 seeds). AIHWKit arm (v2 data, 3 seeds): −1.47pp/10%. "Sweet spot 60–90% ≈ flat" is retracted; correct statement: *graceful linear degradation with a knee at the output-layer boundary*.

## F2 (retracted pending autopsy) — variance-first
numpy: sd at 94.6% frozen (0.0105) < sd at 68.8% (0.0161); F-test p=0.79 (wrong direction). AIHWKit signal driven entirely by seed 2 at 0.388 — *below* the no-adapt floor (~0.45) → fine-tune actively destroyed the network → optimizer-divergence signature, not hardware. Action: log loss traces, re-run that config; delete or re-scope F2.

## F3 (refined) — parallel adapter
Matched-cost wins only in extreme-frozen regime: r2 0.683 vs 96.8%-split 0.628 (+5.5pp, p=0.033, paired); r8 vs 90%-split −2.1pp n.s. r2≈r4 (0.6830 vs 0.6827) → **coverage, not rank**: adapter restores access to all 10 classes where partial-L3 reaches 6. v11 addendum: with fully programmable encoders+decoders the adapter's effect ≈ 0 → it is *insurance conditional on edge baked-ness* (dormant B=0 init = free option).

## F4 (thinned) — drift
Per-seed 1-month deltas: 0%→−4.29pp (p=.004), 68.8%→−5.09 (p=.004), 94.6%→−8.58 (p=.027). Ordering contrasts: 0 vs 68.8 +0.80pp p=.039 (only significant); 68.8 vs 94.6 p=.115; 0 vs 94.6 p=.070. 100%-frozen flat line is definitional (baked assumed drift-free). Adapter "drift resistance" −1.4pp p=.41 = noise.

## F5 (confirmed) — technology-conditional clean-acc inversion
numpy +2.04pp clean acc per 100% frozen (p=.012); AIHWKit +0.01pp (p=.94). Reappears in v11: baked fusion core beats programmable on the comparison head at deploy (0.810 vs 0.743) — write quantization damages delicate functions more than 5% continuous fab noise.

## F6 (confirmed, extended) — conversion dominance → control-plane elimination
F6 energy ladder confirmed in v9 with real charge flow; extension: baking removes the need for per-frame intelligent control (no write-verify, no weight loads at inference) → control plane collapses to a ~4k-gate sequencer (~10µW). See F13.

## F7 (new) — placement beats budget (baking-order experiment, v4)
Orders: forward L1→L2→L3, reverse L3→L2→L1, random columns; 30 seeds, 20-ratio grid.
- Low/mid frozen: reverse (bake classifier, keep input layer tunable) beats forward by +2.0 to +2.3pp (p≤7e-4) at identical cost — the deployment shift is input-space, so correction lives in L1.
- Extreme frozen: forward dominates (reverse collapses to 0.537 vs forward 0.655 at 95.7%) — small budgets are only efficient in the complete output layer.
- Random is worst at high frozen (0.654 vs 0.749 at 90%): scattered tunables = partial control of every layer, full control of none.
- Pareto frontier is order-mixed: forward below ~12.4k cost, random/reverse above.
- v5 caveat: one-position TEXT shift (one-hot permutation, pre-acc 0.02) recovered to 0.93 by output-only tuning → proviso: output-only suffices when shifted representations stay separable; vocabulary size = the knob (queued).

## F8 (new) — the cliff is linear in the right coordinate; boundary tracks architecture
For n_prog ≤ L3: acc = 0.424 + **3.04pp × k** (k = tunable output neurons), R²=0.90; intercept matches measured 100%-frozen floor (0.438); quadratic adds nothing. Scaling test (v8, 4 sizes 1.9k–32k weights, 8 CRN seeds): each size's knee sits at ITS output boundary (93.8/94.6/95.7/97.0%), and per-neuron slope grows with width: 2.17→3.21→3.48→3.98 pp/neuron (more weights per output column). Size D recovers 95% of full-programmable adaptability with output layer only = 3.0% of weights.

## F9 (new) — bigger bakes better (with caveat)
Max frozen at ≥90% recovery: A 60.5% / B 75.3% / C 75.2% / D 90.0%; device cost 0.60×→0.50×→0.50×→0.40×. Caveat: task fixed → larger models more overparameterized; matched-capacity control required before generalizing (queue 13).

## F10 (new) — time-domain encoding kills the 2^N latency (v5)
2^N exists only where a digital value is serialized. Countermeasures, all simulated:
- Input: one-hot binary lines = 1 slot, zero input timing precision required.
- Hidden: continuous pulse chaining (integrator+comparator → pulse width, never a code); knob R = window/jitter. Digits: R=32 → 0.956 (float 0.968), R=64 converged. Clock words (one-hot in): R=8 → 0.980, R=16 → 0.9965 — binary inputs raise first-layer SNR.
- Output: first-spike WTA = analog argmax; matches windowed argmax by R=32; mean decision at 60–70% of window.
- Latency: classic 8-bit interlayer 768 slots → digits pipeline 103 (7.5×) → one-hot clock 43 (18×). Printed @1µs slot: 43µs per inference vs 5ms frame.

## F11 (new) — per-chip head calibration (v7, v12)
After baking L1/L2, measure THIS chip's activations (through real noise) and ridge-solve the linear head; program with write-verify. Effects:
- Absorbs the fab lottery: chips A/B spectrogram corr 0.81/0.67 → 0.859/0.854.
- Absorbs core IR distortion (v12-E4): exact nodal distortion at r=1e-3 (44%/27% per tile) → uncal RMSE +42%; head-recal → **+8% over ideal**. Write-verify sees the distorted world and re-linearizes it.

## F12 (new) — the TTS chip, end to end (v6→v7→v10)
- v7: teacher = espeak-ng + MBROLA us1 (real diphone speech); representation = **LPC-10** (10 reflection coefficients + F0 + gain + voicing @100Hz) — TMS5100/Speak&Spell codec; |k|<1 stability = built-in noise tolerance. Analysis→synthesis ceiling: melspec corr **0.994** (codec transparent). Chips: 0.859/0.854. Drifted head: 0.769 — F4 made audible. Voicing channel = residual bottleneck (float RMSE 0.19; fix: derive from phone identity in control plane — queued).
- Chip: 80 one-hot lines → baked 80×64 + 64×32 → memristor 32×13 (5.5% programmable) → 13 analog pulse-width outputs → all-pole synth. No ADC in signal path.
- F12b RC-causal variant (v10): replace prev/next lookahead context with printed-RC low-passed copies of current phone one-hot (τ=30,100ms): corr **0.874 ≥ 0.859**, 75 lines vs 80, strictly causal (streaming). Claim as parity-at-fewer-lines; the ">" may be vocabulary-scale redundancy (queue 14a). Printed caps inherit ~5% tolerance on τ — enters noise model.

## F13 (new) — power (v9), all from real chip-A conductances and real utterance charge flow
Core 13.0µW @100Hz: periphery 9.0 (69%), drivers 2.4, head 1.44 (mostly OFF-leak: on/off=30 × 832 devices), L2 0.20, L1 0.008, reprogram amortized 0.00014. Duty 1.3%.
Baselines (same 7,584-MAC net): ESP32 SW 6,250µW; M4-class 38; 28nm ASIC 2.5 (unprintable); all-prog analog same-µpower-parts 16.2; F6 research constants 0.04 (technology-class, not comparable).
Control plane: ESP32 always-on 225,000µW; ULP 300; **autonomous sequencer 10 → 23µW system** — uniquely enabled by baking (no per-frame intelligence needed).
Resistance is a free knob: array power spans 5 decades before the 9µW periphery floor; thermal-noise limit for R=32 only at R_unit>758MΩ. Scaling: conversion-elimination advantage shrinks toward large N (per-neuron ADC term grows slower than weights) — baking's energy edge is largest at edge scale, same place its manufacturability edge lives. Leakage corollary: every device moved from head to baked part deletes its leak permanently → leakage-aware frozen-ratio Pareto (queued).

## F14 (new) — multimodal law (v8 → v10 → v11)
- v8 (single-modality-at-a-time, core forced programmable): baked ENCODERS maximize interference (−20.5pp TXT collateral from IMG ft; ping-pong forgetting −21pp) — plasticity forced into the shared resource corrupts it.
- v10 full grid (enc × core baked-ness, dec programmable): **best cell on every axis = programmable encoders + fully BAKED core**: recovery +45.4pp, collateral −0.9pp, forgetting −3.1pp, and cheaper than prog-core neighbor (33 vs 36µW — baked core doesn't leak). Worst: everything-baked-but-decoder (−30.5 collateral). Power flat in #modalities: shared baked-core chip 24.0µW@M=1 → 24.1µW@M=8 (quiescent encoders draw nothing, incl. leak: no voltage, no leak); M separate chips: 192µW@8.
- v11 trimodal fusion (IMG+TXT+AUD mel-16×8 espeak audio; analog sum-bus; heads: fused digit + odd-one-out): baked core costs ~nothing — deploy head1 0.995≈0.994, head2 BETTER baked (0.810 vs 0.743, F5 mechanism); drift restored via encoder-side adaptation alone (0.886); multi-head protection (untouched head 0.880 vs 0.816). **Novel-function test:** never-trained txt-odd class learned post-fab to recall 0.48 (baked) vs 0.51 (prog) vs 0.49 (adapter) — indistinguishable; frozen mixing re-purposable via edge plasticity. All plateau ~0.5 → bottleneck is adaptation data/edge capacity, not the core. Adapter ≈ 0 effect with programmable edges (see F3).
- Open: modality dropout / absent-modality operating-point shift on the sum bus (untested — flagged as prerequisite for trusting flat-power claim end-to-end).

## F15 (new) — IR drop, done exactly (v12)
Exact sparse-Kirchhoff nodal solver (every wordline/bitline segment; differential planes share wordlines = worst-case loading; vectorized assembly; splu + multi-RHS).
- **Correction:** static attenuation mask underestimates true distortion by up to 5× at scale (mask-vs-nodal 0.28 @128/1e-4, 5.5 @256/1e-3). All prior IR nulls are mask-model statements.
- Raw distortion ||W_eff−W||/||W||: @1e-4: 0.021/0.086/0.229/0.509 for 32/64/128/256; @1e-3: 0.17/0.48/0.76/0.92.
- **Linearity theorem (ohmic arrays):** ideal drivers + virtual ground ⇒ network linear ⇒ W_eff exact and input-INDEPENDENT. Input dependence enters only via (a) shared-rail impedance, (b) device nonlinearity (absent for printed R; head-only).
- Compensation: baked continuous fixed-point reaches ~1% residual in feasible regime; 16-level write-quantized floors ~20% (**~10× baked advantage**). Hard wall = conductance clipping: 43% of cells demand >G_MAX at 128/1e-3. (Our elementwise fixed point under-converges in strong regime — residuals there are upper bounds.)
- Rail droop (only input-dependent term): one-hot(4/128) error 0.3–3.0% where dense-50% hits 4.5–32% across R_rail 3e-5–3e-4 → **~15× sparsity margin**.
- Operating points: PB-1 printed board r≈2.4mΩ/1MΩ=2.4e-9 → immune by construction (this is a *consequence of the power study's* high-R choice); DIY sputtered head ~2.5e-4 at 32-wide → tiny, and calibrated anyway; research dense arrays (10kΩ, µm wires) = the literature's real problem.
- E4 head-cal rescue on PB-1: see F11. Caveats: uncal condition used float head (slightly optimistic; cal-vs-ideal is the fair pair); memristor I-V nonlinearity not yet in nodal model (fine at 32-wide, required before scaling the programmable fraction).

## Honest limitations ledger (v2)
Toy tasks (8×8 digits, 24-word vocab, 36-phrase TTS); fixed train/test split (seed spread excludes data variance; 629-image binomial 1σ≈1.7pp); energy constants order-of-magnitude, digital baselines exclude their own I/O; drift = one-shot decay in TTS demo (AIHWKit PCM port queued); adapter not IR-modeled; RC τ tolerance unmodeled; modality dropout untested; nodal model ohmic-only; compensation solver naive; biases in software throughout; per-layer R uniform (independent per-layer sweep queued).
