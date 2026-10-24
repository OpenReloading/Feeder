FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm@sha256:68aef3859e340a2b0cc63260978c5d40e82f48e30fb00503c59cea9104ff8a6b

# libgl for OCP.
RUN apt-get update \
 && apt-get install -y --no-install-recommends procps libgl1 libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*
