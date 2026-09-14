"""Peak RSS / memory measurement for the child process tree."""

try:
    import psutil
except ImportError:
    psutil = None


class PeakMemory:
    """Samples total RSS of a process tree; also reports final peak RSS.

    Use sample() periodically (a thread in the runner) and peak_bytes at
    the end. Falls back to os.wait4-style resource usage if psutil is
    missing (caller must provide rusage max_kb).
    """

    def __init__(self, proc):
        self.proc = proc
        self.peak = 0

    def sample(self):
        if psutil is None or not self.proc or self.proc.poll() is not None:
            return
        try:
            p = psutil.Process(self.proc.pid)
            total = p.memory_info().rss
            for c in p.children(recursive=True):
                try:
                    total += c.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
            self.peak = max(self.peak, total)
        except psutil.NoSuchProcess:
            pass

    def result(self):
        return {"peak_memory_mb": round(self.peak / (1024 * 1024), 2) if self.peak else None}
