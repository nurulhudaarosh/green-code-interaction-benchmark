"""Unit tests for measurement/ (stdlib unittest; also runs under pytest)."""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from measurement.memory import PeakMemory  # noqa: E402
from measurement.rapl import RaplEnergy, available  # noqa: E402
from measurement.system import CpuSampler, machine_info  # noqa: E402


class TestRapl(unittest.TestCase):
    def test_api_contract(self):
        # Whatever the host, the result is always JSON-serialisable and
        # energy is None when RAPL is unavailable.
        rapl = RaplEnergy()
        with rapl:
            pass
        out = rapl.stop()
        self.assertIn("energy_j", out)
        self.assertIn("energy_source", out)
        if not rapl.ok:
            self.assertIsNone(out["energy_j"])
            self.assertEqual(out["energy_source"], "unavailable")
        else:
            self.assertIsInstance(out["energy_j"], float)

    def test_available_returns_bool(self):
        self.assertIsInstance(available(), bool)

    def test_unavailable_domain_falls_back(self):
        rapl = RaplEnergy(domain="intel-rapl:99-does-not-exist")
        self.assertFalse(rapl.ok)
        out = rapl.stop()
        self.assertIsNone(out["energy_j"])


class _DummyProc:
    def poll(self):
        return 0


class TestPeakMemory(unittest.TestCase):
    def test_no_samples(self):
        self.assertEqual(PeakMemory(_DummyProc()).result(),
                         {"peak_memory_mb": None})


class TestCpuSampler(unittest.TestCase):
    def test_empty_result(self):
        out = CpuSampler(pid=None).start().result()
        self.assertIsNone(out["cpu_percent_avg"])
        self.assertIsNone(out["cpu_percent_max"])


class TestMachineInfo(unittest.TestCase):
    def test_keys(self):
        info = machine_info()
        self.assertIn("platform", info)
        self.assertIn("python", info)


if __name__ == "__main__":
    unittest.main()
