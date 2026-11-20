"""Single CPU budget shared by every tool that takes a thread count."""

import os

ENV_THREADS = "ECC_THREADS"


def thread_budget() -> int:
    """``ECC_THREADS`` when it is a positive integer, else the CPUs this process may use."""
    raw = os.environ.get(ENV_THREADS, "").strip()
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:  # platforms without sched_getaffinity
        return max(1, os.cpu_count() or 1)
