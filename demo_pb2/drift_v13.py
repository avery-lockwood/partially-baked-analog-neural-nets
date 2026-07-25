"""
drift_v13.py — physical memristor-head conductance drift over weeks.

Only the programmable memristor HEAD drifts; the baked printed-resistor core
(L1/L2) does not. That asymmetry is the whole point of the thesis: drift
lives in the small tunable part, and the fixed shared part is immune.

Model (per 70_literature_validation.md §3): PCM/RRAM conductance follows the
power law G(t) = G0 * (t/t0)^(-nu), with drift exponent nu ~ N(0.06, s_nu)
distributed PER DEVICE (Joshi et al., Nat. Commun. 2020). We apply it to the
two conductances G+ and G- of each differential head cell SEPARATELY, so the
per-device nu spread turns into a growing *weight distortion*, not merely a
common gain change. Optional global-gain compensation (a single scalar
rescale, the cheapest realistic mitigation) is provided to show how much of
the loss is a recoverable gain vs. irrecoverable distortion.

This reuses v7's verbatim training/synthesis; it only reimplements the head
BAKE so it can expose G+/G- (v7.bake_chip returns only the net weight).

  from drift_v13 import bake_head_full, drift_head, weeks_grid
"""
import numpy as np

import tts_chip_sim_v7 as v7

# device age at programming time, expressed in weeks (~1 hour). Drift is
# measured relative to this reference, so t=T0_WEEKS => no drift.
T0_WEEKS = 1.0 / 168.0


def bake_head_full(model, rng, Xcal, Ycal, ceil):
    """Like v7.bake_chip but returns the baked L1/L2 plus the head's separate
    differential conductances (Gp, Gn), scale, and bias — everything needed to
    drift the head physically. Baking math is identical to v7.bake_chip."""
    Wn = [model.W[0] * (1 + rng.normal(0, v7.SIGMA_FAB, model.W[0].shape)),
          model.W[1] * (1 + rng.normal(0, v7.SIGMA_FAB, model.W[1].shape))]
    # per-chip calibration: measure baked activations through read noise, ridge-solve head
    a = Xcal
    for i in range(2):
        z = a @ Wn[i] + model.b[i]
        a = np.clip(v7.relu(z) + rng.normal(0, ceil[i] / v7.R_LEVELS, z.shape),
                    0, ceil[i])
    A = np.hstack([a, np.ones((len(a), 1))])
    lam = 1e-3 * len(A)
    M = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ Ycal)
    W3, b3 = M[:-1], M[-1]
    # quantize to N_LEVELS with programming noise, as differential conductances
    s = np.abs(W3).max() + 1e-12
    step = 1.0 / (v7.N_LEVELS - 1)
    q = lambda G: np.clip(np.round(G / step) * step
                          + rng.normal(0, v7.SIGMA_PROG, G.shape), 0, 1)
    Gp = q(np.clip(W3, 0, None) / s)
    Gn = q(np.clip(-W3, 0, None) / s)
    return Wn, Gp, Gn, s, b3


def drift_head(Gp, Gn, s, weeks, rng, nu_mean=0.06, nu_sd=0.012, compensate=False):
    """Return the drifted net head weight after `weeks` of aging.
    Per-device nu ~ N(nu_mean, nu_sd) on each conductance separately."""
    if weeks <= 0:
        return (Gp - Gn) * s
    ratio = max(weeks, T0_WEEKS) / T0_WEEKS
    nup = np.clip(nu_mean + nu_sd * rng.standard_normal(Gp.shape), 0, None)
    nun = np.clip(nu_mean + nu_sd * rng.standard_normal(Gn.shape), 0, None)
    Gpd = Gp * ratio ** (-nup)
    Gnd = Gn * ratio ** (-nun)
    W = (Gpd - Gnd) * s
    if compensate:
        # cheapest realistic fix: one global gain rescale to restore weight norm
        W0 = (Gp - Gn) * s
        g = (np.linalg.norm(W0) + 1e-12) / (np.linalg.norm(W) + 1e-12)
        W = W * g
    return W


def drift_head_nu(Gp, Gn, s, weeks, nup, nun, compensate=False):
    """Deterministic drift given explicit per-device exponents nup/nun (same
    shape as Gp/Gn). Used when Python-rendered audio and the in-browser visual
    must apply the *identical* drift — store nup/nun once, use here and in JS."""
    if weeks <= 0:
        return (Gp - Gn) * s
    ratio = max(weeks, T0_WEEKS) / T0_WEEKS
    W = (Gp * ratio ** (-nup) - Gn * ratio ** (-nun)) * s
    if compensate:
        W0 = (Gp - Gn) * s
        g = (np.linalg.norm(W0) + 1e-12) / (np.linalg.norm(W) + 1e-12)
        W = W * g
    return W


def weeks_grid():
    """Week points for the drift series (0 = freshly calibrated)."""
    return [0, 1, 2, 4, 8, 12]
