FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm@sha256:2126b4442a339013517c71ea39fbb5ce7cf058440fac2bebf5db216eacbd55ad

# libgl for OCP.
RUN apt-get update \
 && apt-get install -y --no-install-recommends procps libgl1 libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*

USER vscode
