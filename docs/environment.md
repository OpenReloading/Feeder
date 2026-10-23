# Environment

All builds and tests run in the dev container (`.devcontainer/`).

| Component | Version | Source |
|---|---|---|
| Base image | `mcr.microsoft.com/devcontainers/python:3.2.6-3.12-bookworm` (digest `sha256:589b65db...ffa56`) | Microsoft dev container images |
| Python | 3.12.15 | base image |

Python packages (top-level pins in `pyproject.toml`, full lock in `requirements.txt`):

| Package | Version |
|---|---|
| build123d | 0.13.0 |
| bd_warehouse | 0.4.0 |
| cadquery-ocp-novtk | 8.0.1.1.0 |
| trimesh | 5.1.1 |
| manifold3d | 3.5.4 |
| shapely | 2.2.0 |
| rtree | 1.4.1 |
| numpy | 2.5.4 |
| scipy | 1.18.1 |
| pandas | 3.0.6 |
| matplotlib | 3.11.2 |
| pytest | 9.1.1 |
| ocp_vscode (optional viewer) | 4.2.0 |

Git is used on the host.
