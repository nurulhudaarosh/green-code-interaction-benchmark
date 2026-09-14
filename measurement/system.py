"""System probes: CPU utilisation sampling during measurement."""

try:
    import psutil
except ImportError:
    psutil = None

import time


class CpuSampler:
    """Samples system-wide CPU%% while a program runs; also process CPU%%."""

    def __init__(self, pid=None):
        self.pid = pid
        self.samples = []

    def sample(self):
        if psutil is None:
            return
        try:
            self.samples.append(psutil.cpu_percent(interval=None))
        except Exception:
            pass

    def start(self):
        if psutil is not None:
            psutil.cpu_percent(interval=None)  # reset interval baseline
        return self

    def result(self):
        if not self.samples:
            return {"cpu_percent_avg": None, "cpu_percent_max": None}
        return {
            "cpu_percent_avg": round(sum(self.samples) / len(self.samples), 1),
            "cpu_percent_max": round(max(self.samples), 1),
        }


def machine_info():
    """Static environment description stored with every measurement."""
    info = {}
    if psutil is not None:
        try:
            info["cpu_count"] = psutil.cpu_count()
            freq = psutil.cpu_freq()
            info["cpu_freq_mhz"] = round(freq.current, 0) if freq else None
            info["os"] = psutil._common
        except Exception:
            pass
    import platform
    info["platform"] = platform.platform()
    info["python"] = platform.python_version()
    info.pop("os", None)
    return info
