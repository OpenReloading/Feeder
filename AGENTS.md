# Feeder

Parametric brass and bullet collator for reloading, built in build123d with metric DIN/ISO hardware. License MIT (`LICENSE`).

## Commands

- Agents run on the host; file edits and Git stay there. Start the container with `devcontainer up --docker-path podman --workspace-folder .` (creates `.venv` from `requirements.txt`); run project commands with the prefix `devcontainer exec --docker-path podman --workspace-folder .`.
- Build all parts and run the tests: `.venv/bin/python build.py`
- Build only: `.venv/bin/python build.py --no-test`
- Tests only: `.venv/bin/python -m pytest -q`
- Build guide site: `.venv/bin/pip install -r requirements-guide.txt`, `.venv/bin/python build.py --no-test --guide`, `.venv/bin/mkdocs build --strict`
- Simulation: `.venv/bin/python -m sim run|sweep|plot|calibrate` (README "Simulation"). A sweep runs for hours: at most 4 to 6 workers, never next to the test suite (host memory)

## Conventions

- `feeder/config.py` holds every dimension and option; part modules in `feeder/parts/` use only config values and `feeder/lib/` features, no literal dimensions.
- Each part module exposes `PARTS = {name: builder}`; `build.py` exports each to `build/<name>.stl` and `.step`.
- Critical dimensions carry a one-line source note in `config.py`.
- Lint (as CI, job `lint-python` in `.github/workflows/ci.yml`): `.venv/bin/pip install --only-binary :all: --require-hashes -r requirements-dev.txt`, then `.venv/bin/ruff check .` and `.venv/bin/basedpyright --pythonpath .venv/bin/python` (rules in `pyproject.toml`). `requirements-dev.txt` is compiled from `requirements-dev.in` on Python 3.13: `pip-compile --generate-hashes --strip-extras --output-file=requirements-dev.txt requirements-dev.in`. Existing findings are baselined (`# noqa` comments, `.basedpyright/baseline.json`): fix a new finding, do not add to the baseline. Remove a baseline entry when its code is fixed.
- `reference/` is a local folder, excluded in `.git/info/exclude`. Tracked files never depend on it and never copy from it. Dimensions come from standards, datasheets, caliber data and print tolerances.

## Branches

- `develop` is the default branch. Branch from it and open pull requests against it (squash merge).
- `main` holds releases and is the Pages source. It changes only by a pull request from `develop`, merged with a merge commit.

## Agent skills

### Issue tracker

GitHub Issues in `OpenReloading/Feeder` via `gh`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
