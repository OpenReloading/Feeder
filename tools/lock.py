"""Writes pylock.toml, the lock the dev container and CI install, from the pins of requirements.txt. It holds the wheels
of the dev container (x86_64 Linux, CPython 3.14) whatever the host is. Run after a change of requirements.txt, on the
host or in the container (uv is not part of the locked environment: in the container `pipx install uv` adds it):

    python3 tools/lock.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
# the oldest glibc that has a wheel of every pin (cadquery-ocp-novtk needs 2.28); the container has 2.36
PLATFORM = "x86_64-manylinux_2_28"
PYTHON = "3.14"


def main() -> int:
    uv = shutil.which("uv")
    if uv is None:
        sys.exit("uv is not on the PATH: https://docs.astral.sh/uv/getting-started/installation/")
    # --no-build: a pin without a wheel for PLATFORM stops the run, no source distribution gets locked
    command = [uv, "pip", "compile", "requirements.txt", "--output-file", "pylock.toml", "--no-build"]
    command += ["--python-platform", PLATFORM, "--python-version", PYTHON]
    # --upgrade: the existing pylock.toml is not read, so a broken one (merge conflict) does not stop the run
    command += ["--upgrade"]
    # the same file on any host: no uv configuration files, the index named
    command += ["--no-config", "--default-index", "https://pypi.org/simple"]
    # uv also prints the lock: only its messages (a yanked pin) are shown
    return subprocess.call([*command, "--custom-compile-command", "python3 tools/lock.py"], cwd=ROOT, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    raise SystemExit(main())
