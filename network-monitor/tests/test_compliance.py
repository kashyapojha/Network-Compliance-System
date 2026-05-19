"""
Unit Tests — Network Naming Compliance Monitor
Run: python -m pytest tests/test_compliance.py -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitor import check_compliance

# ─── Compliant hostnames ────────────────────────────────────────────────────
VALID = [
    "IT-WS-0042",
    "HR-LPT-0023",
    "FIN-WS-0099",
    "OPS-SRV-0007",
    "DEV-LPT-2201",
    "MKT-MOB-0450",
    "IT-CAM-0001",
    "DEV-IOT-9999",
]

# ─── Non-compliant hostnames ─────────────────────────────────────────────────
INVALID = [
    ("johns-laptop",   "dept prefix"),
    ("WORKSTATION42",  "dept prefix"),
    ("dev_macbook",    "dept prefix"),
    ("fin-ws-99",      "4-digit ID"),
    ("it-ws-0001",     "uppercase"),
    ("HR-laptop-John", "device type"),
    ("GUEST-PC",       "dept prefix"),
    ("IT-WS-1",        "4-digit ID"),
]


def test_valid_hostnames():
    for name in VALID:
        ok, failures = check_compliance(name)
        assert ok, f"Expected COMPLIANT for '{name}', got failures: {failures}"


def test_invalid_hostnames():
    for name, reason in INVALID:
        ok, failures = check_compliance(name)
        assert not ok, f"Expected VIOLATION for '{name}' (reason: {reason}), but got compliant"
        assert len(failures) > 0


def test_failure_messages():
    _, failures = check_compliance("johns-laptop")
    assert any("dept" in f.lower() or "prefix" in f.lower() or "IT" in f for f in failures)


def test_case_sensitivity():
    ok_upper, _ = check_compliance("IT-WS-0042")
    ok_lower, _ = check_compliance("it-ws-0042")
    assert ok_upper is True
    assert ok_lower is False


def test_length_boundary():
    # Exactly 10 chars
    ok, _ = check_compliance("IT-WS-0042")
    assert ok
    # Too short
    ok2, _ = check_compliance("IT-WS-001")
    assert not ok2


if __name__ == "__main__":
    passed = failed = 0
    tests = [test_valid_hostnames, test_invalid_hostnames,
             test_failure_messages, test_case_sensitivity, test_length_boundary]
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
