"""Points the configurator page's "Source code" link at the commit the site is built from (AGPL section 13).

The page writes the link as https://github.com/OpenReloading/Feeder/tree/@SOURCE_COMMIT@. A build outside a git clone fails.
"""

import subprocess
from pathlib import Path

PLACEHOLDER = "@SOURCE_COMMIT@"


def on_config(config):
    root = Path(config.config_file_path).parent
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    config.extra["source_commit"] = commit


def on_page_markdown(markdown, config, **_):
    return markdown.replace(PLACEHOLDER, config.extra["source_commit"])
