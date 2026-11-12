FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm@sha256:94053b777943a4eda40e83d5386f7c5befb72f5bb778878ac527bb9491adcd42

# libgl for OCP.
RUN apt-get update \
 && apt-get install -y --no-install-recommends procps libgl1 libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*

USER vscode
