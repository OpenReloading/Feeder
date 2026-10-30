# Feeder

Parametric brass and bullet collator for reloading, built in build123d with metric DIN/ISO hardware. Every command and its output: [docs/development.md](docs/development.md).

## Commands

- Agents run on the host; file edits and Git stay there. Start the container with `devcontainer up --docker-path podman --workspace-folder .` (creates `.venv` from `pylock.toml`); run project commands with the prefix `devcontainer exec --docker-path podman --workspace-folder .`.
- Build all parts and run the tests: `.venv/bin/python build.py`. Build only: `.venv/bin/python build.py --no-test`. Tests only: `.venv/bin/python -m pytest -q`.
- Coverage floors: `.venv/bin/python -m pytest -q -n 4 --dist loadfile --cov`, then `.venv/bin/coverage report --rcfile=sim/.coveragerc`. Floors: `fail_under` in `pyproject.toml` (`feeder`) and `sim/.coveragerc` (`sim`). Keep a floor a little below the measured value and raise it when coverage rises. A partial run fails the floor.
- Lock: `pylock.toml` (PEP 751, wheels of Python 3.14, hashes) is what the dev container, CI build, tests and docs install (`pip install -r pylock.toml`). Dependabot updates `requirements.txt`, the pinned input; after that change regenerate the lock in the container with `.venv/bin/pip lock --only-binary :all: -r requirements.txt -o pylock.toml` (`tests/test_lock.py` fails when they differ). Packages held back in the `ignore` list of `.github/dependabot.yml` stay at their `requirements.txt` pins.
- Build guide site: [docs/development.md](docs/development.md#build-guide-site).
- Release ([docs/development.md](docs/development.md#pull-requests-and-releases)): from a clean checkout, `./release-configurator.sh` merges the open release pull request (waits for its checks), builds the configurator's print files from the new tag, attaches `configurator-<tag>.tar.gz` to the release and redeploys the site. `./release-configurator.sh <tag>` only publishes for that release. The workflow `Release weekly` runs only when dispatched (the script does that), never on a schedule. CI does not build the print files; `/next/` (built from `main`) has none.
- Simulation: [docs/development.md](docs/development.md#simulation). A sweep runs for hours: at most 4 to 6 workers, never next to the test suite (host memory).

## Conventions

- `feeder/config.py` holds every dimension and option; part modules in `feeder/parts/` use only config values and `feeder/lib/` features, no literal dimensions.
- Each part module exposes `PARTS = {name: builder}`; `build.py` exports each to `build/<name>.stl` and `.step`.
- Critical dimensions carry a one-line source note in `config.py`.
- Lint (as CI, job `lint-python` in `.github/workflows/ci.yml`): `.venv/bin/pip install --only-binary :all: --require-hashes -r requirements-dev.txt`, then `.venv/bin/ruff check .` and `.venv/bin/basedpyright --pythonpath .venv/bin/python` (rules in `pyproject.toml`). `requirements-dev.txt` is compiled from `requirements-dev.in` on Python 3.13: `pip-compile --generate-hashes --strip-extras --output-file=requirements-dev.txt requirements-dev.in`. Existing findings are baselined (`# noqa` comments, `.basedpyright/baseline.json`): fix a new finding, do not add to the baseline. Remove a baseline entry when its code is fixed.
- `reference/` is a local folder, excluded in `.git/info/exclude`. Tracked files never depend on it and never copy from it. Dimensions come from standards, datasheets, caliber data and print tolerances.

## Branches

- `main` is the only long-lived branch. Branch from it and open pull requests against it (squash merge, linear history). The title follows Conventional Commits (check `conventional`).

## Agent skills

- Issue tracker: GitHub Issues in `OpenReloading/Feeder` via `gh`, see `docs/agents/issue-tracker.md`.
- Triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`, see `docs/agents/triage-labels.md`.
- Domain docs: single context, `GLOSSARY.md` and `docs/adr/`, see `docs/agents/domain.md`.
