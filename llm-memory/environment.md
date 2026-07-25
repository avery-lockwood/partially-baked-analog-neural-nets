# Environment & reproduction

## Stack
Python 3.12 + numpy/scipy/sklearn/matplotlib. `pip install --break-system-packages`
(externally-managed environment). No network datasets needed — sklearn
digits only. AIHWKit used for the analog-tile cross-validation arm (not yet
exercised for the v4-v12 CRN protocol — that port is P0 #1 in the queue).

For bundle 02 (TTS): `apt-get install espeak-ng mbrola mbrola-us1` — install
from the Ubuntu archive works even though this box is otherwise
locked-down/no-root for other packages (see git note below); espeak-ng was
preinstalled in past sessions. `espeak-ng -v us-mbrola-1 --pho` needs the
mbrola voice installed to emit phoneme+timing alignment.

## Sandbox quirks
- Background (`&`) processes get killed between tool calls in this sandbox
  — run long jobs in the foreground with `timeout`.
- The container has persisted across a full working day before, but don't
  rely on that — everything should be regenerable from the bundle
  notebooks (run-all regenerates every script, CSV, and figure).
- A prior session found an unexplained `tts_chip_sim_v7.py` file appear
  mid-session (probably a leftover from a parallel session) — it was
  reviewed line-by-line before execution. Keep that habit: don't execute
  unfamiliar files that show up without a clear origin.

## Git / no-root note (2026-07-25)
This host has no working `sudo` (no askpass/terminal) and the user is not
root, so `apt-get install` fails with a dpkg lock permission error for
anything that needs system-wide installation. Workaround used to get git
installed: `apt-get download <pkg>` still works (fetches the .deb without
needing the dpkg lock), then `dpkg-deb -x <pkg>.deb ~/.local/<name>-install`
extracts it user-locally without root. git's PATH/GIT_EXEC_PATH additions
were appended to `~/.bashrc`. If another tool is needed and normal
`apt-get install` fails the same way, the same download+extract pattern
should work as long as the package doesn't need a postinst script or
setuid bits.

## Docker dev container (2026-07-25) — UP and working
Persistent CPU-only container `analog-nn-dev`, project bind-mounted at
`/workspace` (host `.../analog neural net project` == container
`/workspace`). Has python3.12 + numpy/scipy/sklearn/matplotlib/jupyter +
espeak-ng + mbrola + mbrola-us1. Do project python/jupyter work here, not on
the host. See `.docker/README.md`.

**Invoking it (fresh session):** try
`docker exec -w /workspace/demo_pb2 analog-nn-dev python3 <script>` directly;
if it says "permission denied ... docker.sock", wrap with `sg docker`:
`sg docker -c "docker exec -w /workspace/demo_pb2 analog-nn-dev python3 <script>"`
(this worked all session without a Claude Code restart). Gotchas:
- The container runs as ROOT → files it writes into the bind mount are
  root-owned (avery can read/commit them but can't delete/overwrite from the
  host; regenerate via the container).
- Long jobs take ~3-5 min (a ~156s corpus-load dominates); run them in the
  background. Weak CPU (4 cores) — keep concurrency low. 24g memory cap.

Host specs: AMD Ryzen 3 2200G (4 cores, weak), 32GB RAM, GTX 1070 GPU on the
`nouveau` driver — no CUDA yet; switching to the proprietary driver + wiring
`--gpus all` into the container is deferred (needs a reboot; Avery prefers
the low-risk path). `.docker/setup_docker.sh` did the one-time host setup
(run WITHOUT a sudo prefix, else it adds root not avery to the docker
group — already fixed in the script).
