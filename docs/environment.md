# Environment

All builds and tests run in the dev container (`.devcontainer/`).

| Component | Version | Source |
|---|---|---|
| Base image | `mcr.microsoft.com/devcontainers/python:3.14-bookworm` (digest `sha256:94053b77...d42`) | Microsoft dev container images |
| Python | 3.14.8 | base image |

Python packages (top-level pins in `pyproject.toml`, full lock in `pylock.toml`):

| Package | Version |
|---|---|
| build123d | 0.13.0 |
| bd_warehouse | 0.4.0 |
| cadquery-ocp-novtk | 8.0.1.1.0 |
| trimesh | 5.2.2 |
| manifold3d | 3.5.5 |
| networkx | 3.7 |
| shapely | 2.2.0 |
| rtree | 1.4.1 |
| numpy | 2.5.4 |
| scipy | 1.18.1 |
| pandas | 3.1.1 |
| matplotlib | 3.11.2 |
| pytest | 9.2.0 |
| pytest-xdist | 3.8.0 |
| pytest-cov | 7.1.0 |
| ocp_vscode (optional viewer) | 4.3.0 |
| mujoco (simulation) | 4.0.1 |
| coacd (simulation) | 1.0.14 |

Git is used on the host.
