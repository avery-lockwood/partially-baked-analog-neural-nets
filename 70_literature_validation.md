# 70 — Literature Validation of Simulation Assumptions

*Created 2026-07-25. Purpose: map every load-bearing device/noise assumption
and headline result in the partial-baking analog-NN simulation
(`demo_pb2/tts_chip_sim_v7.py`, bundles 01–03) to **real, published,
citable numbers**, and state honestly where our numbers are optimistic,
pessimistic, or reasonable. This is the "validation that cites data from
other papers" the paper needs (see `60_demo_and_paper_goals.md`).*

**Honesty rule for this doc:** every number below was found via web search
and is attributed to a specific paper with a URL/DOI. Where I could not find
published support, it is listed in **§8 Gaps / still need** rather than
papered over. Where our sim is more optimistic than the literature, the
verdict says so in plain language.

**Sim constants under validation** (from `tts_chip_sim_v7.py` line 30):
`SIGMA_FAB = 0.05`, `SIGMA_PROG = 0.04`, `N_LEVELS = 16` (write levels),
`R_LEVELS = 32` (time-domain read levels), `P = 10` (LPC order). Drift model:
head weights relax to `0.65·W + 0.35·mean` (line 301). IR model: exact nodal
solver (v12), printed device resistance 1–10 MΩ.

---

## 1. Device fabrication variability — SIGMA_FAB = 5%, SIGMA_PROG = 4%

**(a) Our numbers.** Baked devices carry ~5% relative multiplicative weight
noise (`SIGMA_FAB=0.05`); the programmable memristor head carries ~4%
programming noise (`SIGMA_PROG=0.04`), applied as additive Gaussian on the
normalized conductance.

**(b) Published numbers.**

- **Joshi et al., *Nature Communications* 11, 2473 (2020)** — "Accurate deep
  neural network inference using computational phase-change memory."
  Programmed-conductance error had **median σ ≈ 0.94 µS on a 0–25 µS range**,
  i.e. **~3.8% of full-scale**, "less than 1.2 µS" across all levels. Effective
  precision "roughly 4-bit." 99.1% of devices programmed successfully.
  [nature.com/articles/s41467-020-16108-9](https://www.nature.com/articles/s41467-020-16108-9)
  · open text: [PMC7235046](https://pmc.ncbi.nlm.nih.gov/articles/PMC7235046/)
- **"Achieving high precision in analog in-memory computing systems," *npj
  Unconventional Computing* (2025)** — device conductance modeled as Gaussian
  about the target with **standard deviation swept 0%–6% of max conductance**;
  systems "maintain correct outputs for conductance variations up to 5%," and
  "beyond 5%" accumulated errors start producing wrong decisions. PCM cells
  show **initial conductance spread under 6%** and **relative read/current
  noise under 9%**.
  [nature.com/articles/s44335-025-00044-2](https://www.nature.com/articles/s44335-025-00044-2)
  · open text: [PMC12779548](https://pmc.ncbi.nlm.nih.gov/articles/PMC12779548/)
- **"Reliability of analog resistive switching memory for neuromorphic
  computing," *Applied Physics Reviews* 7, 011301 (2020)** (Ielmini group) —
  RRAM conductance spread scales as **σ_R/R ∝ R^0.5** (Poissonian filament
  defects); low-conductance states are proportionally noisier.
  [pubs.aip.org/aip/apr/article/7/1/011301](https://pubs.aip.org/aip/apr/article/7/1/011301/997403/Reliability-of-analog-resistive-switching-memory)
- **Rasch et al., *APL Machine Learning* 1, 041102 (2023)** — the IBM AIHWKit,
  whose PCM/RRAM presets are fitted to the published device data above and
  which models programming noise, read noise, and drift as first-class effects.
  [pubs.aip.org/aip/aml/article/1/4/041102](https://pubs.aip.org/aip/aml/article/1/4/041102/2923573/Using-the-IBM-analog-in-memory-hardware)
  · kit: [github.com/IBM/aihwkit](https://github.com/IBM/aihwkit)

**(c) Verdict — WELL SUPPORTED, and arguably slightly optimistic for the
programmable head.** Our `SIGMA_PROG=4%` sits almost exactly on Joshi's
measured ~3.8%-of-full-scale programming error and inside the npj review's
"correct up to 5%" band. This is the best-anchored assumption in the sim.
Two honesty caveats: (i) the literature spread is often quoted *relative to
max conductance* (full-scale) while our sim applies it *multiplicatively per
weight after clipping* — the semantics differ and our per-weight noise on
small weights is effectively gentler than a full-scale σ; and (ii) real RRAM
variability is conductance-dependent (σ_R/R ∝ R^0.5), which our single flat
σ does not capture — low-weight devices are noisier in reality than in our
model. For the **baked** core, `SIGMA_FAB=5%` is defensible as an analog-IMC
device number, but its *right* justification is the printed-resistor
literature in §4, not the memristor literature.

---

## 2. Write levels / quantization — N_LEVELS = 16 (4-bit)

**(a) Our number.** 16 distinct programmable conductance levels on the head
(`N_LEVELS=16`), i.e. **4-bit** weights, quantized as
`round(G/step)·step + N(0,SIGMA_PROG)`.

**(b) Published numbers.**

- **Joshi et al., Nat. Commun. 2020** — practical PCM precision "roughly
  **4-bit**" per weight after programming noise. Directly matches our 16 levels.
  [PMC7235046](https://pmc.ncbi.nlm.nih.gov/articles/PMC7235046/)
- **Rao et al., *Nature* 615, 823 (2023)** — "Thousands of conductance levels
  in memristors integrated on CMOS": **2,048 levels (11-bit)** demonstrated on
  256×256 foundry-CMOS-integrated arrays — but only with a tailored
  write-verify programming protocol, denoising, and read-optimized biasing.
  [nature.com/articles/s41586-023-05759-5](https://www.nature.com/articles/s41586-023-05759-5)
- **Song/Rao et al., *Science* 383, 903 (2024)** — "Programming memristor
  arrays with arbitrarily high precision": high effective precision by using a
  *weighted sum of several low-precision devices*, later devices compensating
  earlier programming error. I.e. many-level precision is an
  architecture/protocol achievement, not a raw single-device property.
  [science.org/doi/10.1126/science.adi9405](https://www.science.org/doi/10.1126/science.adi9405)
  · [PubMed 38386733](https://pubmed.ncbi.nlm.nih.gov/38386733/)
- Multi-level (>16-state) single devices also demonstrated in graphene
  memristive synapses ([PMC7596564](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7596564/)).

**(c) Verdict — REASONABLE / mildly conservative for a single device, honest
about the head.** 16 levels (4-bit) is exactly the *routine, no-heroics*
precision reported for PCM/RRAM (Joshi). Papers reporting 11-bit / "thousands
of levels" do exist, but they require write-verify loops, multi-device
encoding, and careful biasing — infrastructure our baked-core thesis
deliberately avoids on the programmable head. So 16 levels is a fair, even
slightly conservative, choice for a *simple* programmable head, and it is the
honest number to cite: we are **not** claiming the 2,048-level best case. If
anything, note in the paper that the head could be pushed higher at the cost
of the write-verify machinery the design is trying to minimize.

---

## 3. Conductance drift — accuracy loss over ~1 month

**(a) Our model.** Drift is modeled on the programmable head as a relaxation
`W3 → 0.65·W3 + 0.35·sign(W3)·mean(|W3|)` (a pull of every weight toward a
common magnitude), producing an audible "drifted chip A." Findings ledger F4
reports per-seed 1-month accuracy deltas of roughly **−4 to −9 pp** depending
on frozen ratio; the fully-baked core is drift-free by construction.

**(b) Published numbers.**

- **Joshi et al., Nat. Commun. 2020** — PCM conductance drifts as
  **G(t) = G(t₀)·(t/t₀)^−ν** with drift exponent **ν ≈ 0.06 on average**,
  Gaussian-distributed across devices and state-dependent (amorphous drifts
  more than crystalline). With drift compensation, CIFAR-10 held **>93.5% after
  1 day** and ImageNet ResNet-34 **>71% extrapolated to 1 year** — i.e. a few
  points of loss over months, not collapse.
  [PMC7235046](https://pmc.ncbi.nlm.nih.gov/articles/PMC7235046/)
- **Le Gallo et al., "A 64-core mixed-signal in-memory compute chip based on
  PCM," (2022)** — hardware-measured drift + noise on a real inference chip.
  [arxiv.org/abs/2212.02872](https://arxiv.org/pdf/2212.02872)
- **"Reducing the impact of PCM conductance drift on inference of large-scale
  hardware neural networks," IEDM/IEEE (2020)** — drift + ν-variability drives
  a monotonic accuracy decrease; compensation (global + adaptive batch scaling)
  recovers most of it (e.g. ~7% recovered at 1 year in one method).
  [ieeexplore.ieee.org/document/8993482](https://ieeexplore.ieee.org/document/8993482/)

**(c) Verdict — DIRECTIONALLY SUPPORTED but our drift model is a caricature,
not a physical fit.** The *phenomenon* (memristor/PCM heads lose a few points
of accuracy over weeks–months while a truly fixed element does not) is solidly
published, and the F4 magnitude (single-digit-pp loss over a month) is in the
right ballpark vs. Joshi's compensated retention. **However**, the sim's
`0.65·W + 0.35·mean` relaxation is a hand-chosen contraction, *not* the
physical `t^−ν` power law with ν≈0.06 and per-device ν-variability. It is fine
as an *audible demo* of "drift happens to the tunable part," but the paper
should either (i) label it explicitly as a qualitative caricature, or (ii)
replace it with the AIHWKit PCM drift+compensation model for a quantitative
claim (this is exactly queue item "drift-over-weeks with real AIHWKit PCM
model"). Also flag the load-bearing idealization: **the baked core is assumed
perfectly drift-free**; printed/thin-film resistors are far more stable than
memristors (§4) but not literally infinitely stable.

---

## 4. Printed / thin-film resistor tolerance & stability — the "baked" 5%

**(a) Our claim.** The baked core is "shared and stable — it neither drifts,
nor leaks, nor suffers IR drop," modeled with the same `SIGMA_FAB=5%`
fabrication spread and *no* drift term.

**(b) Published numbers.**

- **Standard thick-film resistors:** tolerance **±1% to ±5%**, TCR ±100–200
  ppm/°C, after trimming. Untrimmed *embedded* thin-/polymer-thick-film
  resistors are worse — **~±10%**.
  ("Preliminary assessment of the stability of thin- and polymer thick-film
  resistors embedded into printed wiring boards," *Microelectronics
  Reliability* — [sciencedirect S0026271412001102](https://www.sciencedirect.com/science/article/abs/pii/S0026271412001102);
  "Stability of miniaturized non-trimmed thick- and thin-film resistors,"
  [sciencedirect S0026271418301252](https://www.sciencedirect.com/science/article/abs/pii/S0026271418301252))
- **Screen-printed / flexible printed resistors:** "a nonstandard *precise*
  screen-printing process provides tolerance of resistivity **less than 5%**"
  (no trimming needed), but ordinary screen printing is imprecise and
  predictability is low at aspect ratios below ~0.5 squares.
  ("Printed resistors for flexible electronics—thermal variance mitigation and
  tolerance improvement via oxide–metal coatings," *Engineering Research
  Express* 2020 — [iopscience 10.1088/2631-8695/abbae0](https://iopscience.iop.org/article/10.1088/2631-8695/abbae0))
- Industry framing: matching conventional-resistor initial tolerance,
  long-term stability, and power handling is an *open challenge* for printed
  electronics (same IOP/ScienceDirect sources).

**(c) Verdict — SUPPORTED at the optimistic edge; 5% is achievable but is a
*good-process* number, not a *typical screen-print* number.** The published
"precise screen printing < 5%" result and "thick film ±1–5%" band vindicate
`SIGMA_FAB=5%` as attainable, and crucially the **stability** half of the
claim is real: fired thick/thin-film resistors are dramatically more drift-
and retention-stable than any memristor, which is the whole "bake what is
stable" argument. Honest caveats for the paper: (i) *typical* untrimmed
printed resistors run ~±10%, so 5% assumes either trimming or a controlled
process (Avery's sputter rig plausibly qualifies for thin-film, but this
should be stated as a process requirement, not a freebie); (ii) 5% is a
*static* fabrication spread — the design's key advantage is that this spread
is then absorbed by per-chip head calibration (F11), which is what actually
makes the 5% tolerable rather than the 5% being intrinsically tight. Frame it
as "5% is buildable AND we calibrate through it," not "5% is easy."

---

## 5. LPC-10 vocoder intelligibility & precision tolerance

**(a) Our claim.** LPC reflection coefficients are bounded |k|<1 (lattice
filter stable for any such k) and precision-tolerant, "which is why LPC
vocoders survived 4–6 bit quantization in the 70s" (TMS5100 / Speak & Spell).
Sim uses P=10 reflection coeffs + F0 + gain + voicing per 10 ms frame.

**(b) Published numbers.**

- **TI TMS5100 / Speak & Spell (1978) LPC-10 format:** **54-bit frames**; per-
  frame excitation params + **10 reflection coefficients** with bit allocation
  **6, 6, 5, 5, 4, 4, 4, 4, 3, 3 bits** for k1…k10 — i.e. the higher-order
  coefficients really are coded at **3–4 bits** and remain intelligible.
  Synthesis is an **order-10 all-pole lattice**; coefficients/energies stored
  in ROM from an analysis-by-synthesis search.
  ("Speech synthesis algorithms," Mutable Instruments tech notes —
  [pichenettes.github.io/…/speech_synthesis_algorithms](https://pichenettes.github.io/mutable-instruments-documentation/tech_notes/speech_synthesis_algorithms/);
  "How it Works — Bringing Back the Voice of Speak & Spell," Adafruit —
  [learn.adafruit.com/bringing-back-the-voice-of-speak-spell/how-it-works](https://learn.adafruit.com/bringing-back-the-voice-of-speak-spell/how-it-works))
- **Government-standard LPC-10 / LPC-10e (FS-1015)** ran intelligible speech at
  **2.4 kbit/s** on order-10 LPC — the canonical evidence that order-10 LPC is
  robust at very low bit rates.
- **Wong et al., "Optimal quantization performance of LPC parameters for speech
  coding," Eurospeech 1989** — quantifies how few bits per LPC parameter still
  preserve quality (reflection/LSF quantization sensitivity).
  [isca-archive.org/eurospeech_1989/wong89](https://www.isca-archive.org/eurospeech_1989/wong89_eurospeech.html)

**(c) Verdict — STRONGLY SUPPORTED, and it is the historical bedrock of the
whole demo.** The "survived 4–6 bit quantization" claim is not hand-waving:
the TMS5100 bit allocation literally codes reflection coefficients at 3–6 bits
and shipped in a mass-market intelligible product, and LPC-10 at 2.4 kbit/s is
a documented standard. The |k|<1 stability property is a textbook fact about
the lattice realization. This directly motivates why analog noise (our
`SIGMA_*`, our R_LEVELS read quantization) is survivable in the *output
representation*: a representation engineered to tolerate 3-bit quantization
tolerates a few-percent analog perturbation. One nuance to state: our sim's
**0.86 spectrogram-fidelity** headline is a correlation metric, not a
standardized intelligibility score (e.g. no DRT/MOS listening test was run),
so the *heritage* claim is airtight but our own *intelligibility* claim rests
on a proxy — see §8.

---

## 6. IR drop in crossbar arrays — negligible at 1–10 MΩ printed devices

**(a) Our claim.** The v12 exact nodal solver shows IR distortion, but choosing
**high device resistance (1–10 MΩ, printed)** makes the per-segment resistance
ratio r_seg → ~1e-9, so IR drop is "immune by construction"; low-R regimes
need pre-compensation (baked-only ~10× advantage) until conductance clipping.
Finding F15: a static-mask approximation *underestimated* true IR distortion
by up to ~5×, which the exact solver corrects.

**(b) Published numbers.**

- **Severity when device R is low:** finite wire resistance is catastrophic in
  the low-R regime — one 1S1R crossbar analysis reports inference accuracy
  **collapsing to 38.5%** when wire resistance is ignored in design vs. **85.9%**
  when properly accounted, and prescribes **device on-resistance ~100–200 kΩ**
  to keep IR drop minimal for 64×64 / 128×128 arrays.
  ("In-Depth Analysis of One Selector–One Resistor Crossbar Array … with Finite
  Wire Resistance," *Adv. Intelligent Systems* / ResearchGate —
  [researchgate 356411581](https://www.researchgate.net/publication/356411581))
- **Line-resistance modeling:** the classic exact treatment — Chen, "A
  Comprehensive Crossbar Array Model With Solutions for Line Resistance and
  Nonlinear Device Characteristics," *IEEE TED* (2013) — establishes nodal
  line-resistance solving as the correct method (validating our v12 exact
  solver over static masks).
  [researchgate 258792710](https://www.researchgate.net/publication/258792710)
- **Design rule agreement:** the npj "Achieving high precision in AIMC" review
  and the variability tutorial both state IR drop becomes significant as wire
  resistance approaches device on-resistance, so **raising device resistance
  (and lowering it via fatter wires) is the primary IR mitigation** — exactly
  our "exit, don't mitigate" rule.
  [PMC12779548](https://pmc.ncbi.nlm.nih.gov/articles/PMC12779548/);
  variability tutorial [arxiv 2204.09543](https://arxiv.org/pdf/2204.09543)

**(c) Verdict — SUPPORTED, with the important framing that our advantage comes
from an operating-point choice the mainstream can't always make.** The
literature agrees on the mechanism (IR drop matters when R_device is not >>
R_wire) and on the fix (high device resistance). The published "minimal IR"
target is **~100–200 kΩ**; our printed devices at **1–10 MΩ** are 5–100× higher
still, so "IR drop negligible" is quantitatively credible — printed
electronics *forces* a high-R operating point, turning a liability into
immunity. Two honest points: (i) mainstream memristor/PCM work sits at low R
(kΩ range) for speed/density and *therefore* fights IR drop — our immunity is
bought by giving up their speed/density, a trade the paper should state, not
hide; (ii) our nodal solver is **ohmic-only** (no memristor I–V nonlinearity,
naive strong-regime compensation, per methods §"Known gaps"), so the *low-R*
compensation results are weaker than the *high-R* immunity result. Lead with
the high-R immunity claim (strong) and hedge the compensation claim (modeled,
not device-accurate).

---

## 7. Time-domain / pulse-width analog compute — one-hot encoding, no converters

**(a) Our claim.** One-hot / binary time-domain input encoding plus continuous
pulse-width chaining between layers avoids input DACs and per-frame ADCs,
kills converter latency and IR sensitivity simultaneously (F10), with read
quantization abstracted as R_LEVELS = 16–32.

**(b) Published numbers.**

- **Yamaguchi, Iwamoto, Tamukoh & Morie (Kyushu Inst. Tech.), "An Energy-
  efficient Time-domain Analog VLSI Neural Network Processor Based on a Pulse-
  Width Modulation Approach," arXiv:1902.07707 (2019)** — PWM time-domain
  weighted-sum in **250 nm CMOS**, **~300 TOPS/W** (projected >1,000 TOPS/W),
  computing via capacitor charge/discharge timing **without op-amps and without
  A/D–D/A conversion**; reported **±1% weighted-sum deviation**, ~1.5% mean /
  8% max error on ReLU outputs.
  [arxiv.org/abs/1902.07707](https://arxiv.org/pdf/1902.07707)
- **Miyashita et al., "A PWM-based Dot-Product Engine for Neuromorphic
  Computing using Memristor Crossbar Array," IEEE ISCAS (2017)** — PWM inputs to
  a memristor crossbar reduce peripheral (ADC/DAC) power and area vs. amplitude-
  mode. [ieeexplore.ieee.org/document/8351276](https://ieeexplore.ieee.org/document/8351276/)
- CMOS time-domain analog spiking neuron circuits (area/power-efficient,
  op-amp-free) — [arxiv 2208.11881](https://arxiv.org/pdf/2208.11881) — and
  temporal-coding SNN VLSI — [arxiv 2001.05348](https://arxiv.org/pdf/2001.05348).

**(c) Verdict — SUPPORTED as an established design direction; our specific
one-hot-input twist is a reasonable, lightly-differentiated contribution.**
Time-domain/PWM analog compute that eliminates converters and op-amps is
well-established prior art (Morie group's ~300 TOPS/W is the headline number to
cite), so our F10 "kills converter latency/IR sensitivity" claim is credible
and not novel *in kind*. The genuinely distinctive pieces to position against
this prior art are (i) **one-hot binary inputs** specifically (zero input-timing
precision, higher first-layer SNR — our F10 notes R=8 already gives 0.980 on
one-hot clock words), and (ii) coupling time-domain encoding to the **baked/
programmable split**. Honest note: the cited works report measured silicon
(TOPS/W, error) whereas our R_LEVELS is an *abstraction* over
integrator/comparator specs with "circuit mapping not yet done" (methods
§time-domain) — so we can cite them for feasibility but should not claim our
efficiency numbers are silicon-validated.

---

## 8. Gaps / still need (assumptions with weak or missing published support)

Honest ledger of what is **not** yet backed by a citable external number:

1. **Drift model is a caricature, not a fit.** We cite the PCM `t^−ν`, ν≈0.06
   law (§3) but our sim uses an ad-hoc `0.65·W+0.35·mean` relaxation. *Need:*
   re-run drift with the AIHWKit PCM drift+ν-variability model to make any
   quantitative "accuracy after 1 month" claim (queue item already logged).
2. **`SIGMA_FAB` semantics vs. literature semantics.** Published spreads are
   usually quoted as % of *max/full-scale* conductance and are *conductance-
   dependent* (σ_R/R ∝ R^0.5); our sim applies a flat multiplicative per-weight
   σ. Numerically close, but not the same statistical object — *need* a short
   methods paragraph reconciling the two, or a conductance-dependent noise term.
3. **Printed-resistor 5% is a good-process number.** Typical untrimmed printed
   resistors are ~±10% (§4). *Need:* either a citation for Avery's specific
   sputtered thin-film process tolerance, or state 5% as a process *target/
   requirement* the build must hit (with calibration absorbing the rest).
4. **No standardized intelligibility test.** The LPC *heritage* is airtight,
   but our own output quality is reported as a 0.86 mel-spectrogram correlation,
   not a DRT/MOS/word-accuracy listening test. *Need:* a small listening-test or
   ASR-word-accuracy proxy to make an intelligibility (not just fidelity) claim.
5. **Baked core assumed perfectly drift-free and leak-free.** Defensible
   relative to memristors, but "infinitely stable" is an idealization; no cited
   number bounds printed-resistor long-term drift under bias/thermal cycling.
   *Need:* a thin-film-resistor long-term-stability (ppm/1000h) citation.
6. **IR nodal solver is ohmic-only.** High-R immunity is solid; the low-R
   *compensation* result (baked ~10× advantage) uses naive strong-regime
   compensation and no device I–V nonlinearity (methods §known gaps). *Need:*
   nonlinear device model before leaning on the compensation claim.
7. **R_LEVELS (16–32) has no circuit mapping.** Cited time-domain silicon
   (§7) shows the approach works, but our read-resolution knob is an
   abstraction; *need* an integrator/comparator noise budget to tie R_LEVELS to
   real specs.

---

### One-line scorecard

| # | Assumption | Sim value | Verdict |
|---|---|---|---|
| 1 | Prog. noise `SIGMA_PROG` | 4% | **Well supported** (~3.8% measured, Joshi) |
| 1 | Fab noise `SIGMA_FAB` (analog-IMC) | 5% | **Supported**, at optimistic edge |
| 2 | Write levels | 16 (4-bit) | **Reasonable/conservative** (4-bit routine; 11-bit needs heroics) |
| 3 | Drift over ~1 month | ad-hoc relaxation | **Directionally right, model is a caricature** |
| 4 | Printed resistor tolerance | 5%, drift-free | **Supported as good-process target**; typical ~10% |
| 5 | LPC noise-tolerance / heritage | 3–6 bit RCs | **Strongly supported** (TMS5100 6,6,5,5,4,4,4,4,3,3) |
| 6 | IR drop negligible @1–10 MΩ | high-R immunity | **Supported**; solver ohmic-only |
| 7 | Time-domain, no converters | one-hot + PWM | **Supported prior art** (~300 TOPS/W, Morie) |
