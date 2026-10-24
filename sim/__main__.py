"""CLI: `run` one point, `sweep` a grid into build/sim/sweep.csv, `plot` it to PNG, `calibrate` against hardware.

- sweep appends rows and skips points already in the CSV, so a stopped sweep resumes.
- calibrate reads a CSV of measured points (tilt, rpm, cases_per_h, base_down_share), runs each at every mu and
  com_ratio of the grid and writes the error per pair, best first. Set the best pair in `config.py`.
"""

import argparse
import csv
import itertools
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from sim.run import run

OUT = Path(__file__).parent.parent / "build" / "sim"
KEYS = ("plate", "case", "tilt", "rpm", "cases", "com_ratio", "mu", "seed")
TEXT = ("plate", "case")


def _floats(s: str) -> list[float]:
    return [float(v) for v in s.split(",")]


def _done(path: Path) -> set[tuple]:
    if not path.exists():
        return set()
    with path.open() as f:
        rows = csv.DictReader(f)
        if not set(KEYS) <= set(rows.fieldnames or ()):
            raise SystemExit(f"{path} has other columns (older model): pass a new --out")
        return {tuple(r[k] if k in TEXT else float(r[k]) for k in KEYS) for r in rows}


def sweep(a) -> None:
    path = Path(a.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    done = _done(path)
    todo = [dict(plate=pl, case=a.case or None, tilt=t, rpm=r, n_cases=a.cases, revs=a.revs, com_ratio=c, mu=m, seed=s)
            for pl, t, r, c, m, s in itertools.product(a.plate.split(","), _floats(a.tilt), _floats(a.rpm), _floats(a.com), _floats(a.mu),
                                                       range(1, a.seeds + 1))
            if (pl, a.case, t, r, a.cases, c, m, s) not in done]
    print(f"{len(todo)} points to run, {len(done)} done", flush=True)
    # submit `run` itself: under forkserver and spawn a function defined in `__main__` is not importable in the worker
    with ProcessPoolExecutor(max_workers=min(a.workers, 6)) as ex:  # each worker holds a 250 case pile; the host has about 10 GB free
        for fut in as_completed([ex.submit(run, **kw) for kw in todo]):
            row = fut.result()
            new = not path.exists()
            if not new:
                with path.open() as f:
                    if next(csv.reader(f)) != list(row):
                        raise SystemExit(f"{path} has other columns (older model): pass a new --out")
            with path.open("a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(row))
                if new:
                    w.writeheader()
                w.writerow(row)
            print(json.dumps(row), flush=True)


def plot(a) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with open(a.csv) as f:
        rows = [r for r in csv.DictReader(f) if r["valid"] == "True"]  # a lost or spilled case is a model fault
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
    for tilt in sorted({float(r["tilt"]) for r in rows}):
        rs = sorted((r for r in rows if float(r["tilt"]) == tilt), key=lambda r: float(r["rpm"]))
        x = [float(r["rpm"]) for r in rs]
        ax[0].plot(x, [float(r["cases_per_h"]) for r in rs], "o-", label=f"{tilt:g} deg")
        ax[1].plot(x, [float(r["fill"]) for r in rs], "o-")
        ax[1].fill_between(x, [float(r["fill_lo"]) for r in rs], [float(r["fill_hi"]) for r in rs], alpha=0.2)
        ax[2].plot(x, [float(r["torque_p95"]) for r in rs], "o-")
    for a_, label in zip(ax, ("base-down exits per hour", "pocket fill (95 % CI)", "plate torque p95, Nm")):
        a_.set_xlabel("plate rpm")
        a_.set_title(label)
        a_.grid(alpha=0.3)
    ax[0].legend(title="tilt")
    fig.tight_layout()
    out = Path(a.csv).with_suffix(".png")
    fig.savefig(out, dpi=120)
    print(out)


def calibrate(a) -> None:
    with open(a.measured) as f:
        measured = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    pairs = list(itertools.product(_floats(a.mu), _floats(a.com)))
    jobs = [dict(tilt=m["tilt"], rpm=m["rpm"], n_cases=a.cases, revs=a.revs, mu=mu, com_ratio=c) for mu, c in pairs for m in measured]
    with ProcessPoolExecutor(max_workers=min(a.workers, 6)) as ex:
        sims = [f.result() for f in [ex.submit(run, **kw) for kw in jobs]]
    out = []
    for k, (mu, c) in enumerate(pairs):
        err = 0.0
        for m, s in zip(measured, sims[k * len(measured):(k + 1) * len(measured)]):
            share = s["base_down"] / s["exits"] if s["exits"] else 0.0
            err += ((s["cases_per_h"] - m["cases_per_h"]) / m["cases_per_h"]) ** 2 + (share - m["base_down_share"]) ** 2
        out.append(dict(mu=mu, com_ratio=c, error=round(err, 4)))
    out.sort(key=lambda r: r["error"])
    path = OUT / "calibration.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(json.dumps(out[0]), path)


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m sim", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="one point, metrics as JSON")
    r.add_argument("--tilt", type=float, default=45.0)
    r.add_argument("--rpm", type=float, default=1.5)
    r.add_argument("--seconds", type=float, help="plain run without warm-up (quick look)")
    for q in (r, sub.add_parser("sweep", help="grid into a CSV"), sub.add_parser("calibrate", help="fit mu and com_ratio")):
        q.add_argument("--cases", type=int, default=250)
        q.add_argument("--revs", type=float, default=3.0, help="counted plate turns after the warm-up")
        if q is not r:
            q.add_argument("--mu", default="0.3")
            q.add_argument("--com", default="0.36")
            q.add_argument("--workers", type=int, default=4)
    s = sub.choices["sweep"]
    s.add_argument("--tilt", default="38,45,52,62")
    s.add_argument("--plate", default="9mm_luger", help="plate sets (case_plate.caliber), comma separated")
    s.add_argument("--case", default="", help="case of calibers.table on every plate (default: each plate's envelope case)")
    s.add_argument("--rpm", default="0.75,1.5,3,6.5")
    s.add_argument("--seeds", type=int, default=1)
    s.add_argument("--out", default=str(OUT / "sweep.csv"))
    sub.choices["calibrate"].add_argument("measured", help="CSV with tilt, rpm, cases_per_h, base_down_share")
    sub.choices["calibrate"].set_defaults(mu="0.2,0.3,0.4", com="0.33,0.36,0.39")
    pl = sub.add_parser("plot", help="PNG next to the CSV")
    pl.add_argument("csv", nargs="?", default=str(OUT / "sweep.csv"))
    a = p.parse_args()
    if a.cmd == "run":
        print(json.dumps(run(a.tilt, a.rpm, a.cases, a.revs, seconds=a.seconds)))
    else:
        {"sweep": sweep, "plot": plot, "calibrate": calibrate}[a.cmd](a)


if __name__ == "__main__":
    main()
