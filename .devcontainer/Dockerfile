FROM mcr.microsoft.com/devcontainers/python:3.15-bookworm@sha256:25ac34e3c1a4c5b19a89ece73ed0278e92afc1cfd25ecb51714891e82bede421

# libgl for OCP.
RUN apt-get update \
 && apt-get install -y --no-install-recommends procps libgl1 libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*

USER vscode
