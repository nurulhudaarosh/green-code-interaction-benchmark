"""Child-process sandbox: resource limits + hard kill.

Runs the measurement driver as a subprocess with CPU-time and address-space
limits; the parent enforces a wall-clock timeout and samples memory/CPU.
This is NOT a security sandbox (generated code runs as the same user); it
bounds runaway loops/memory so one bad program cannot hang the pipeline.
"""

import os
import signal
import subprocess
import sys
import threading
import time

from measurement.memory import PeakMemory
from measurement.system import CpuSampler


def make_limits(mem_mb: int):
    def _limits():
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
        if mem_mb:
            resource.setrlimit(resource.RLIMIT_AS, (mem_mb * 1024 * 1024,) * 2)
        os.setpgrp()
    return _limits


def run_capped(cmd, timeout_s: int, mem_mb: int = 4096, cwd=None, env=None):
    """Run cmd, return (stdout_text, stderr_text, resource_metrics, timed_out)."""
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,  # never let generated code block on a tty
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
        env=env,
        preexec_fn=make_limits(mem_mb),
    )
    peak = PeakMemory(proc)
    sampler = CpuSampler(proc.pid).start()
    stop = threading.Event()

    def poller():
        while not stop.wait(0.25):
            peak.sample()
            sampler.sample()

    t = threading.Thread(target=poller, daemon=True)
    t0 = time.perf_counter()
    t.start()
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = proc.communicate()
    finally:
        stop.set()
        t.join(timeout=2)

    wall = round(time.perf_counter() - t0, 6)
    metrics = {"wall_ms": round(wall * 1000, 3), "returncode": proc.returncode,
               "timed_out": timed_out}
    metrics.update(peak.result())
    metrics.update(sampler.result())
    return stdout, stderr, metrics, timed_out
