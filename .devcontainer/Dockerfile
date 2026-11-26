FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm@sha256:6ed8a83ed447d20613b2a7160c710f70426c41f904da9a6c3a546c4c9f30f303

# libgl for OCP.
RUN apt-get update \
 && apt-get install -y --no-install-recommends procps libgl1 libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*

USER vscode
