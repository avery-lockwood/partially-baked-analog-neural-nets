# 20_METHODS_ENV_v2 — methods & environment additions, v4–v12
*Keywords: CRN, SeedSequence, McNemar, ridge, LPC, Levinson, vocoder, nodal, splu, espeak, mbrola, sandbox*

## Statistical protocol (v4, mandatory for all future contrasts)
- CRN: `np.random.SeedSequence([seed, condition_invariant_keys...])` spawned per stage (device noise / column choice / fine-tune shuffle separately). Conditions being contrasted share keys → identical draws.
- Paired per-seed tests (ttest_1samp on deltas); report 95% CIs. Never compare group means of unpaired noisy runs.
- Per-sample correctness vectors saved (`post_vectors_v4.npz`) → McNemar for within-test-set power.
- Plateau claims require trend tests (per-seed OLS slope), not eyeballing; n=5 resolves only ≥5pp.

## Time-domain forward model (v5+, used by TTS chip)
- Activation → pulse width; per-layer window T; jitter N(0, T/R) added per stage; clip at ceiling (99.5th-pct train activation, design-time calibration). Input: one-hot = exact 1-slot; analog = slot-quantized + jitter.
- First-spike WTA: I_j = z_j + B (B = |min z|+margin), t_j = K/I_j, relative jitter 1/R; winner = min t.
- R is an abstraction over integrator/comparator specs; circuit mapping not yet done.

## TTS pipeline (v7 definitive)
- Teacher: `espeak-ng -v us-mbrola-1` per PHRASE; alignment from `--pho` (phoneme + ms durations + pitch points; requires mbrola voice).
- Analysis @8kHz, 25ms/10ms: LPC-10 via Levinson-Durbin (reflection coefficients clipped ±0.98), F0 autocorr 60–320Hz (voiced if peak ratio>0.30), gain=sqrt(residual), F0 interpolated through unvoiced (voicing gates).
- Targets: k'=(k+1)/2 to [0,1]; loss weights [1×10, 3(F0), 2(gain), 3(voicing)].
- Bake: L1/L2 ×(1+N(0,5%)); head: per-chip ridge calibration on baked+jittered activations (λ=1e-3·n), then 16-level+4% write. R=32 hidden, R_out=64.
- Synthesis: k→a (step-up recursion), all-pole lattice, pulse train (energy-normalized sqrt(FS/f0)) / noise excitation, 3-frame smoothing, voicing median.
- Objective proxy: 24-mel log-spectrogram correlation vs original. Ceiling 0.994 = codec transparent.

## Power model (v9)
Array E = V²·Σ(G_active)·t_pulse from REAL weights & activations; memristor leak = N_dev·G_max/onoff whenever stage sees voltage; periphery = per-channel bias × window duty; drivers = CV² clocks + trace edges; control scenarios separate. All constants declared in script header as order-of-magnitude assumptions.

## Nodal IR solver (v12)
- Nodes: wordline + bitline junction per device; M×2N (differential planes share wordline). Vectorized COO assembly; `scipy.sparse.linalg.splu`; M RHS at once (unit drive per row) → exact W_eff = Ip−In.
- 128×128 ≈ 3s; 256×256 ≈ 38s. Compensation: elementwise fixed point G←G·(target/W_eff) damped [0.5,2], 4 iters, per plane; report residual + clip fraction. Rail droop: damped fixed point Vd←0.7Vd+0.3·v·(1−R_rail·ΣVd·g_row).
- Known gaps: ohmic-only (no memristor I-V), naive compensation in strong regime, drivers/sense as large fixed conductances (1e4).

## Multimodal machinery (v8/v10/v11)
- v8 class MM (2 encoders, round-robin); v11 class Tri: 3 encoders, normalized analog SUM BUS h=(hi+ht+ha)/3, dual heads, optional parallel adapter (A rand 0.1, B zero), gradient clipping (norm 5), lr 0.03. Audio modality: espeak word wavs → 16-mel × 8 slices, min-max normed.
- Stage power: modality gating → encoder active_share=1/M; quiescent = no dynamic AND no leak (no voltage).

## Sandbox environment (additions)
- apt from archive.ubuntu.com works: `apt-get install espeak-ng mbrola mbrola-us1` (espeak-ng was preinstalled).
- Background `&` processes are killed between tool calls — run long jobs foreground with `timeout`.
- Container persisted across one full working day this session; do NOT rely on it — everything regenerable from the bundle notebooks.
- An unexplained tts_chip_sim_v7.py appeared mid-session (probably a prior parallel session); reviewed line-by-line before execution — keep that habit.
- pip needs --break-system-packages; no dataset downloads (sklearn digits only); AIHWKit not exercised this session (CRN port = queue #1).
