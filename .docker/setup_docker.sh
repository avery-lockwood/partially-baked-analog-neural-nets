#!/usr/bin/env bash
# One-time host setup for the analog NN project's dev container.
#
# RUN THIS YOURSELF, INTERACTIVELY: it needs your sudo password, which
# Claude cannot supply non-interactively. After it finishes, log out and
# back in (or run `newgrp docker` in your current shell) so your user's new
# `docker` group membership takes effect — after that, docker commands
# (including the ones Claude runs) work without sudo.
#
# Usage: bash setup_docker.sh
set -euo pipefail

PROJECT_DIR="/home/shares/private/analog neural net project"
DOCKER_DIR="$PROJECT_DIR/.docker"
IMAGE_NAME="analog-nn:latest"
CONTAINER_NAME="analog-nn-dev"

echo "== Installing Docker Engine (skips if already installed) =="
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
else
    echo "docker already present: $(docker --version)"
fi

# Target the real invoking user even if this script was run with a `sudo`
# prefix (in which case $(whoami) would wrongly resolve to root).
TARGET_USER="${SUDO_USER:-$(whoami)}"
echo "== Adding $TARGET_USER to the docker group =="
sudo usermod -aG docker "$TARGET_USER"

echo "== Building the project image =="
sudo docker build -t "$IMAGE_NAME" -f "$DOCKER_DIR/Dockerfile" "$DOCKER_DIR"

echo "== (Re)starting the persistent dev container =="
sudo docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
sudo docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --memory 24g \
    -v "$PROJECT_DIR:/workspace" \
    -w /workspace \
    "$IMAGE_NAME" \
    sleep infinity

echo
echo "Done. Container '$CONTAINER_NAME' is running with $PROJECT_DIR mounted at /workspace."
echo
echo "IMPORTANT: log out and back in (or run 'newgrp docker') so docker"
echo "commands work without sudo from here on. Then verify with:"
echo "  docker exec $CONTAINER_NAME python3 --version"
echo "  docker exec $CONTAINER_NAME jupyter --version"
