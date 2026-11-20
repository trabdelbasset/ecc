import os

import pytest

from chipcompiler.utility.threads import ENV_THREADS, thread_budget


def test_budget_defaults_to_the_affinity_set(monkeypatch):
    monkeypatch.delenv(ENV_THREADS, raising=False)
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: {0, 1, 2})
    assert thread_budget() == 3


def test_env_threads_overrides_affinity(monkeypatch):
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: {0, 1, 2})
    monkeypatch.setenv(ENV_THREADS, "5")
    assert thread_budget() == 5


@pytest.mark.parametrize("value", ["", "0", "-2", "abc", "1.5"])
def test_invalid_env_threads_falls_back_to_affinity(monkeypatch, value):
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: {0, 1})
    monkeypatch.setenv(ENV_THREADS, value)
    assert thread_budget() == 2
