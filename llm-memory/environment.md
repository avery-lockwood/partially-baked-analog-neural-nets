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

## Docker dev container (2026-07-25) — the real fix for the no-root problem
Set up a persistent CPU-only Docker container (`analog-nn-dev`) for running
notebooks/scripts in this project, specifically to route around the no-sudo
problem above. See `.docker/README.md` in the project root for day-to-day
usage. Host specs: AMD Ryzen 3 2200G (4 cores, weak), 32GB RAM, GTX 1070
GPU (currently on the `nouveau` driver — no CUDA yet; switching to the
proprietary driver + wiring `--gpus all` into the container is a deferred,
separate step since it needs a reboot). Once the container is running,
Claude should do `docker exec analog-nn-dev ...` for python/jupyter work in
this project rather than running things directly on the host — no root
workarounds needed inside the container. `.docker/setup_docker.sh` has to
be run by Avery herself (needs an interactive sudo password); after it
runs she needs to log out/in (or `newgrp docker`) for her (and Claude's)
shell to pick up passwordless docker access.
