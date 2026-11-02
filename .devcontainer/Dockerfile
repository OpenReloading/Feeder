FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm@sha256:68aef3859e340a2b0cc63260978c5d40e82f48e30fb00503c59cea9104ff8a6b

# libgl for OCP.
RUN apt-get update \
 && apt-get install -y --no-install-recommends procps libgl1 libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*

# Node 26 (site/.nvmrc) for the guide site.
RUN curl -fsSLo /tmp/node.tar.xz https://nodejs.org/dist/v26.13.0/node-v26.13.0-linux-x64.tar.xz \
 && echo 'd28a96af6c38596f6d9d97c0ee531c13d238d757742387d1928de822d959e997  /tmp/node.tar.xz' | sha256sum -c - \
 && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 --exclude='*.md' --exclude=LICENSE \
 && rm /tmp/node.tar.xz

USER vscode
