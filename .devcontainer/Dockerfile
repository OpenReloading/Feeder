FROM mcr.microsoft.com/devcontainers/python:3.2.6-3.12-bookworm@sha256:589b65db720b03c96d721706005f176ff467ee879f92c2d137c04a537feffa56

# libgl for OCP.
RUN apt-get update \
 && apt-get install -y --no-install-recommends procps libgl1 libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*
