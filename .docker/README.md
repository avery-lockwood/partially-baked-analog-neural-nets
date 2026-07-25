# Dev container

CPU-only Python/Jupyter environment for this project, run in a persistent
Docker container named `analog-nn-dev`. Built to work around the host
having no working non-interactive sudo (see
`../llm-memory/environment.md`) — once this is set up, running notebooks
and scripts doesn't need sudo or per-package install workarounds at all.

## One-time setup (Avery runs this, not Claude)
```
bash setup_docker.sh
```
Needs your sudo password interactively, so Claude can't run it. Installs
Docker Engine, adds your user to the `docker` group, builds the image, and
starts the container with the project folder bind-mounted at `/workspace`.
**Log out and back in (or `newgrp docker`) afterward** so docker commands
work without sudo — including the ones Claude will run.

## Day to day
The project root is bind-mounted, not copied, so edits from either side
(host or container) show up immediately in both. Typical commands:
```
docker exec analog-nn-dev python3 some_script.py
docker exec analog-nn-dev jupyter nbconvert --to notebook --execute --inplace bundle_01_validation_scaling.ipynb
docker exec -it analog-nn-dev bash   # interactive shell
```
Container restarts automatically (`--restart unless-stopped`) if the host
reboots. Memory capped at 24g (of 32g host RAM) as a safety margin so a
runaway job can't OOM the host.

## Rebuilding after Dockerfile changes
```
docker build -t analog-nn:latest -f Dockerfile .
docker rm -f analog-nn-dev
bash setup_docker.sh   # or re-run just the docker run part
```

## GPU (not set up yet)
Host GPU is a GTX 1070 currently bound to the `nouveau` driver — no CUDA
until the host switches to NVIDIA's proprietary driver (needs enabling
`contrib`/`non-free` apt components, installing `nvidia-driver`,
blacklisting `nouveau`, and a reboot). That's intentionally deferred as a
separate, riskier step. Once done: install `nvidia-container-toolkit` on
the host, run `sudo nvidia-ctk runtime configure --runtime=docker`, switch
the Dockerfile's `FROM` to an `nvidia/cuda:*-runtime-ubuntu24.04` base, and
add `--gpus all` to the `docker run` in `setup_docker.sh`.
