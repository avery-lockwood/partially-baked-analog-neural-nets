# CPU-only dev environment for the analog NN project.
# Project files are bind-mounted at /workspace at run time (not COPYed here),
# so this image stays small and rebuilds fast on the host's Ryzen 3 2200G.
#
# GPU note: the host GPU (GTX 1070) currently runs the nouveau driver, not
# the proprietary NVIDIA driver, so CUDA isn't available yet. Once that's
# switched (separate step, needs a reboot), swap the FROM line for an
# nvidia/cuda base, add nvidia-container-toolkit on the host, and pass
# `--gpus all` at `docker run` time.
FROM python:3.12-slim-bookworm

# mbrola-us1 (TTS voice data) lives in Debian's non-free component, which
# isn't enabled by default in this base image. Handle both possible apt
# source formats (deb822 debian.sources, or classic sources.list).
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's/^Components: .*/Components: main contrib non-free non-free-firmware/' \
            /etc/apt/sources.list.d/debian.sources; \
    fi; \
    if [ -f /etc/apt/sources.list ]; then \
        sed -i 's/ main$/ main contrib non-free non-free-firmware/' /etc/apt/sources.list; \
    fi

RUN apt-get update && apt-get install -y --no-install-recommends \
        espeak-ng \
        mbrola \
        mbrola-us1 \
        git \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        numpy \
        scipy \
        scikit-learn \
        matplotlib \
        pandas \
        jupyterlab \
        notebook \
        nbconvert \
        papermill \
        ipykernel

WORKDIR /workspace
CMD ["sleep", "infinity"]
