"""Intel RAPL energy measurement (joules) with safe fallback.

Reads energy_uj counters from /sys/class/powercap/intel-rapl*. Returns None
when RAPL is unavailable (e.g. Colab / non-Intel), so callers always get a
JSON-serializable result.
"""

import time
from pathlib import Path

RAPL_GLOB = "/sys/class/powercap/intel-rapl*:*"
DOMAIN = "intel-rapl:0"  # whole package


def available(domain: str = DOMAIN) -> bool:
    base = Path("/sys/class/powercap") / domain
    try:
        return base.is_file() or (base / "energy_uj").read_text() is not None
    except (OSError, PermissionError):
        return False


class RaplEnergy:
    """Context manager: measures package energy delta in joules."""

    def __init__(self, domain: str = DOMAIN):
        self.path = Path("/sys/class/powercap") / domain / "energy_uj"
        self.max_path = Path("/sys/class/powercap") / domain / "max_energy_range_uj"
        self.start = None
        self.t0 = None
        self.ok = self.path.is_file()

    def __enter__(self):
        if self.ok:
            try:
                self.start = int(self.path.read_text())
            except (OSError, PermissionError):
                self.ok = False
                return self
            self.t0 = time.perf_counter()
        return self

    def stop(self):
        if not self.ok:
            return {"energy_j": None, "avg_power_w": None,
                    "energy_source": "unavailable"}
        try:
            end = int(self.path.read_text())
        except (OSError, PermissionError):
            return {"energy_j": None, "avg_power_w": None,
                    "energy_source": "unavailable"}
        dt = time.perf_counter() - self.t0
        delta = end - self.start
        if delta < 0 and self.max_path.is_file():  # counter wrapped
            delta += int(self.max_path.read_text())
        joules = delta / 1e6
        return {
            "energy_j": round(joules, 6),
            "avg_power_w": round(joules / dt, 3) if dt > 0 else None,
            "energy_source": "intel_rapl",
        }

    def __exit__(self, *exc):
        return False
