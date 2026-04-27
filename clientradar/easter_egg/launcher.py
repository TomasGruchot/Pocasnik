from __future__ import annotations

import subprocess
import sys


def launch_easter_egg() -> subprocess.Popen:
    """Launch easter egg game in a separate process."""
    return subprocess.Popen(
        [sys.executable, "-m", "clientradar.easter_egg"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

