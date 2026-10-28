# Development

Building, testing, the build guide site and the simulation. The design reference is in [design.md](design.md).

## Build and test

Run in the container (prefix `devcontainer exec --docker-path podman --workspace-folder .`):

| Command | Result |
|---|---|
| `.venv/bin/python build.py` | builds every part into `build/<name>.stl` and `.step`, then runs the tests |
| `.venv/bin/python build.py --no-test` | builds only |
| `.venv/bin/python build.py --assembly` | also `build/assembly/`: `feeder.step` (part tree), `feeder.3mf` and `viewer.html` (3D assembly steps with every fastener) |
| `.venv/bin/python build.py --variants` | also `build/variants/<split>/` for each `body.split`: body parts and plate, with an `assembly/` folder |
| `.venv/bin/python build.py --plates` | also `build/plates/<set>/` for each plate set: plate, exit insert, drop tube and the drop chain parts |
| `.venv/bin/python build.py --configurator` | also `build/configurator/`: the print files of every option combination (body split, plate set, extender, tilt link, tube shape, hub) as `<hash>.stl`, identical parts stored once, and `manifest.json` with the part files and BOM rows per choice |
| `.venv/bin/python -m pytest -q` | tests only. `-n 4 --dist loadfile` runs the test files on 4 cores |
| `.venv/bin/python -m pytest -q -n 4 --dist loadfile --cov`, then `.venv/bin/coverage report --rcfile=sim/.coveragerc` | tests with a coverage summary and the floors (after the test run, `.venv/bin/coverage xml -o coverage.xml --rcfile=/dev/null` writes the report SonarCloud reads to `coverage.xml` at the root: without the settings of `pyproject.toml` it holds `feeder` and `sim` with paths from the root): `feeder` in `[tool.coverage.report]` of `pyproject.toml` (pytest fails below it), `sim` in `sim/.coveragerc` (the second command). CI (`pages.yml`) runs both on the whole suite. Raise a floor when coverage rises, keep it a little below the measured value. Not measured: `sim/__main__.py` (CLI of the hours-long sweeps). `feeder/export.py` (assembly viewer export) runs only in `build.py --assembly`, so its tests-only coverage is low |

## Build guide site

The build guide is a MkDocs site with the [BuildGuide](https://github.com/OpenReloading/BuildGuide) plugin (`mkdocs.yml`, pages in `guide/`): introduction and BOM checklist from `feeder/guide.py`, the assembly viewer, tilt and capacity from `docs/design.md`. Nothing generated is committed. In the container:

```
.venv/bin/pip install -r requirements-guide.txt
.venv/bin/python build.py --no-test --guide   # build/guide/buildguide.json, guide/generated/assembly/
.venv/bin/mkdocs build --strict               # site/
```

`.github/workflows/pages.yml` runs the tests and builds the guide on every pull request (job `build`, a required check). A push to `main`, a published release and a manual run build both editions into one site and deploy it to GitHub Pages: `main` goes to `/next/` (jobs `build`, `configurator`) and the latest release, built from its tag, to the root (jobs `stable-site`, `stable-configurator`). Until the first release exists the root redirects to `/next/`. If a build job fails, nothing is deployed. The `github-pages` environment must allow deployments from `main` and from the release tags (`v*`). `site_url` in `mkdocs.yml` reads `SITE_URL`.

The configurator page (`guide/configurator.md`, `guide/javascripts/configurator.js`) picks the options, lists the parts and the BOM for the choice and zips the print files in the browser. It reads `build/configurator/` through `hooks/configurator_files.py`: run `build.py --no-test --configurator` before `mkdocs build` to see it locally. A push to `main` builds those files in CI in the job `configurator` (its own runner, so the tests do not compete with it); other builds and local builds without them show a notice instead.

`build/<name>.stl` and `.step` are in the modelled orientation (assembly frame for the body). `build/print/<name>.stl` is each part as it goes on the bed (`feeder/printing.py`): flipped where it prints upside down, turned across the bed diagonal where it is wider than the bed.


## Simulation

`sim/` simulates brass on the turning plate in MuJoCo (`pip install -e .[sim]`, already in `pylock.toml`) and estimates cases per hour, pocket fill, case orientation at the exit and plate torque for a tilt and plate speed. It runs slower than real time (about 3 to 4 s of computing per simulated second with 250 cases), so a sweep takes hours. In the container:

| Command | Result |
|---|---|
| `.venv/bin/python -m sim run --tilt 45 --rpm 1.5` | one point after one warm-up turn, metrics as JSON |
| `.venv/bin/python -m sim sweep --tilt 38,45,52,62 --rpm 0.75,1.5,3,6.5` | grid into `build/sim/sweep.csv`; a stopped sweep resumes, at most 6 workers |
| `.venv/bin/python -m sim sweep --tilt 40,60 --rpm 1.5 --start dumped,tilt_change` | other starts of the pile (below), `--start` takes `settled`, `dumped`, `tilt_change`, `dumped_tilt_change`, `stacked` |
| `.venv/bin/python -m sim run --tilt 0 --rpm 6 --cases 40 --seconds 4 --start stacked --wiper-h 1.5` | the wiper arm in the model (`track.wiper_h`), a two case column over every pocket in the 60 deg before the exit (below) |
| `.venv/bin/python -m sim sweep --plate 9mm_luger,small_pistol --case 9mm_luger --out build/sim/pockets.csv` | one case size on several plate sets (`--plate` takes `case_plate.caliber` values, `--case` a `calibers.table` key) |
| `.venv/bin/python -m sim plot` | `build/sim/sweep.png`: cases per hour, fill with its 95 % interval, torque |
| `.venv/bin/python -m sim calibrate measured.csv` | fits friction and case centre of mass to hardware runs (columns `tilt`, `rpm`, `cases_per_h`, `base_down_share`) into `build/sim/calibration.csv` |

`valid` is false when a case went through the deck outside the opening (`lost`, with where in `lost_at`): a model fault, so `plot` leaves the point out. `spilled` counts cases over the wall from the first step (`spilled_at`, the first 50), `overfill` the cases that found no room below the wall top on their way back. The extender is fitted (`extender`) when `--cases` is more than the wall holds at the steeper of the tilt and the tilt the run starts at (`layout.capacity`). `deepest_mm`, `deepest_pair` and `deep_share` (share of checks with a contact overlap above 1.5 mm) show how far the soft contacts give.
`wrong_upper` is the upper bound on cases leaving mouth down or sideways.
`standing` and `doubles` count, once per pass, the cases in the exit zone (the gate lap angles either side of the exit, the opening's radii) that stand upright above pocket level and the cases with another case directly above them. They count from the first counted step, in the `stacked` start from the first step. The wiper arm is in the model when `track.wiper_h` is set.

Approximations, so take the numbers as trends until calibrated:

- The plate collider is a convex decomposition of the CAD plate (CoACD): hulls reach up to 0.26 mm into the pockets (`sim.pocket_hull_threshold`) and up to 0.8 mm into the air elsewhere (`sim.hull_threshold`).
- Deck, band, gate and wall are boxes round the bowl (`sim.segments`).
- A case is a capsule against other cases, with flat end discs against the feeder. Two cases on top of each other have round ends on each other: at a working tilt the upper one slides off its column within about 0.1 s, so stacks and standing cases did not reach the exit in the runs so far and `standing` and `doubles` stayed 0, also with `--start stacked`. The wiper is therefore tested on the flat plate (`--tilt 0`), where the columns ride to it.
- One friction value (`case_plate.drag_mu`) for every contact. Case mass and centre of mass (`sim.case_mass`, `sim.com_ratio`) are estimates, unverified.

Results (250 9mm cases, 9mm plate, wall 125, about 3 counted turns per point, one seed). Cases per hour and pocket fill:

| Tilt | 0.75 rpm | 1.5 rpm | 3 rpm | 6.5 rpm |
|---|---|---|---|---|
| 38 deg | 885, 59 % | 1,920, 63 % | 2,700, 45 % | 6,500, 49 % |
| 45 deg | 1,005, 67 % | 1,920, 63 % | 2,640, 43 % | 3,770, 28 % |
| 52 deg | 660, 44 % | 1,320, 44 % | 1,920, 31 % | 2,860, 22 % |
| 62 deg (extender) | 375, 25 % | 510, 17 % | 660, 11 % | 520, 4 % |

- Wall falling at 15 deg: every point is valid, and every case left base down, about 600 exits in all. Plate torque peaks at 0.72 Nm, below the low slip estimate of 0.84 Nm.
- Case centre of mass at 0.33 and 0.39 of the length from the base (38 and 45 deg, 1.5 and 3 rpm) moves the rate between 1,200 and 3,780 per hour, still all base down. The farther the centre of mass from the base, the lower the fill.
- 9mm cases on the small_pistol plate (larger pockets) at 45 deg: 1,650 per hour at 1.5 rpm and 2,400 at 3 rpm, all base down.

The results above and in the three bullets are from the wall that fell at 15 deg. With the current wall (top falling at 15 deg, 45 mm floor, `body.heap_angle` 25) and the 200 deg extender leaning 25 deg, 250 cases, one seed, every point valid and every exit base down. Start `settled`, spills counted from the first step, none in any run:

| Tilt | 1.5 rpm | 3 rpm |
|---|---|---|
| 40 deg | 1,920, 63 % | 2,880, 47 % |
| 45 deg | 1,530, 50 % | 2,880, 47 % |
| 60 deg (extender) | 360, 12 % | 1,020, 17 % |

Other starts, 1.5 rpm, cases spilled of 250 (cases per hour). Spills count from the first step, none in any run:

| Start | 40 deg | 45 deg | 60 deg (extender) |
|---|---|---|---|
| `dumped`: all 250 hit the plate together at the speed of a fall from the wall top | 0 (1,800) | 0 (1,710) | 0 (810) |
| `tilt_change`: settled at the far end of 40 to 60 deg, then the tilt changes in 1 s (extender fitted) | 0 (1,620) | not run | 0 (630) |
| `dumped_tilt_change`: dumped at the far end, then the tilt change | 0 (1,500) | not run | 0 (570) |

`dumped` with the extender fitted at 40 and 45 deg: 0 spilled (1,530 and 1,560). The dump starts the pile on the plate with the fall speed along gravity, it does not pour a stream over the rim, so a pour from beyond the high wall is not simulated.

## Pull requests and releases

Pull request titles follow Conventional Commits (`feat:`, `fix:`, `docs:`, ...), because the squash merge uses the title as the commit message and the check `conventional` verifies it. release-please keeps one release pull request open from those commits, and every Monday at 14:00 Europe/Berlin it is merged automatically once its checks pass, which tags the version and creates the GitHub Release. Put the label `hold` on the release pull request to skip a week, or run the workflow `Release weekly` by hand to release on another day.
