"""
Shared pytest setup: markers, and a memory budget for the run.

Headless Chrome is the only memory-hungry thing the suite runs. Measured
2026-09-11 as PSS (which splits shared pages fairly): a Chrome print or DOM dump
peaks at ~470MB, a test worker at ~95MB even mid-sweep, a Deno KaTeX pre-render
at ~70MB. Uncapped, every xdist worker can be inside a Chrome test at once —
12 × ~0.6GB swamped a 7.8GB machine into swap.

So before the run the budget (``PIT_TEST_MEM_MB``, default 4096) is cut to what
is actually free, then split into a worker count (for ``-n auto``) and a number
of Chrome slots (``PIT_CHROME_SLOTS``, honoured by
``worksheets.generate.run_chrome``). A short budget is warned about up front.
"""

from __future__ import annotations

import os

import pytest

_BUDGET_MB = int(os.environ.get("PIT_TEST_MEM_MB", "4096"))
_CHROME_MB = 500
_WORKER_MB = 100
_HEADROOM_MB = 512  # always left free for the rest of the machine

_PLAN = pytest.StashKey[dict]()


def _available_mb() -> int | None:
    """MemAvailable from /proc/meminfo; None where there is no /proc."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return None


def _budget_mb() -> int:
    avail = _available_mb()
    return _BUDGET_MB if avail is None else min(_BUDGET_MB, avail - _HEADROOM_MB)


def pytest_xdist_auto_num_workers(config):
    """``-n auto``: a worker per core, as far as the budget allows while leaving
    room for at least one Chrome. Defers to xdist when its own env var is set."""
    if os.environ.get("PYTEST_XDIST_AUTO_NUM_WORKERS"):
        return None
    fits = (_budget_mb() - _CHROME_MB) // _WORKER_MB
    return max(1, min(os.cpu_count() or 1, fits))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "schemas: core object schema construction and validation"
    )
    config.addinivalue_line("markers", "instantiate: engine.instantiate() behaviour")
    config.addinivalue_line("markers", "rate: verifier.rate() and CA marking")
    config.addinivalue_line("markers", "failure_modes: named exception hierarchy")
    config.addinivalue_line(
        "markers", "scope: F1 in-scope predicate guard + sweep (no out-of-scope draws)"
    )

    if hasattr(config, "workerinput"):
        return  # workers inherit the controller's PIT_CHROME_SLOTS
    # xdist has resolved -n auto by now (pytest_cmdline_main), so this is a count
    workers = max(1, getattr(config.option, "numprocesses", 0) or 0)
    budget = _budget_mb()
    fits = max(1, (budget - workers * _WORKER_MB) // _CHROME_MB)
    os.environ.setdefault("PIT_CHROME_SLOTS", str(fits))
    slots = int(os.environ["PIT_CHROME_SLOTS"])
    config.stash[_PLAN] = {
        "avail": _available_mb(),
        "budget": budget,
        "workers": workers,
        "slots": slots,
        "peak": workers * _WORKER_MB + slots * _CHROME_MB,
    }


def _gb(mb: int) -> str:
    return f"{mb / 1024:.1f}GB"


def pytest_report_header(config):
    plan = config.stash.get(_PLAN, None)
    if plan is None:
        return None
    free = "unknown" if plan["avail"] is None else _gb(plan["avail"])
    return (
        f"memory: {free} free, budget {_gb(plan['budget'])} -> "
        f"{plan['workers']} workers, {plan['slots']} Chrome at a time "
        f"(~{_gb(plan['peak'])} peak; PIT_TEST_MEM_MB / PIT_CHROME_SLOTS to change)"
    )


def pytest_sessionstart(session):
    """Warn before any test runs (even under -q, which hides the header) when
    free memory is short of the budget or the plan overshoots it."""
    plan = session.config.stash.get(_PLAN, None)
    if plan is None:
        return
    short = plan["avail"] is not None and plan["avail"] - _HEADROOM_MB < _BUDGET_MB
    over = plan["peak"] > plan["budget"]
    if not (short or over):
        return
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    if tr is None:
        return
    why = (
        f"only {_gb(plan['avail'])} free, so the {_gb(_BUDGET_MB)} test budget "
        f"is cut to {_gb(plan['budget'])}"
        if short
        else f"the test budget is {_gb(plan['budget'])}"
    )
    tr.write_line(
        f"WARNING: {why}; this run may peak at ~{_gb(plan['peak'])} "
        f"({plan['workers']} workers, {plan['slots']} Chrome at a time). "
        "Close something or pass a smaller -n if the machine starts to swap.",
        yellow=True,
        bold=True,
    )
