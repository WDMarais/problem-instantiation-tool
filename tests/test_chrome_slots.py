"""
Chrome slots — ``worksheets.generate._chrome_slot``.

Each headless Chrome costs ~0.5GB, so the test suite caps how many run at once
(tests/conftest.py sets ``PIT_CHROME_SLOTS`` from its memory budget). The cap is
a set of ``flock``ed files shared by every process; these tests pin that it
really holds.
"""

from __future__ import annotations

import threading
import time

from worksheets.generate import _chrome_slot


def test_slots_cap_how_many_run_at_once(tmp_path):
    active = peak = 0
    count = threading.Lock()

    def job():
        nonlocal active, peak
        with _chrome_slot(2, tmp_path):
            with count:
                active += 1
                peak = max(peak, active)
            time.sleep(0.2)
            with count:
                active -= 1

    threads = [threading.Thread(target=job) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert peak == 2


def test_a_failing_holder_frees_its_slot(tmp_path):
    try:
        with _chrome_slot(1, tmp_path):
            raise RuntimeError("chrome died")
    except RuntimeError:
        pass
    done = threading.Event()

    def job():
        with _chrome_slot(1, tmp_path):
            done.set()

    threading.Thread(target=job, daemon=True).start()
    assert done.wait(2), "the only slot stayed held after its holder raised"


def test_no_cap_when_slots_is_zero(tmp_path):
    with _chrome_slot(0, tmp_path), _chrome_slot(0, tmp_path):
        pass  # nested: would deadlock if a slot were taken
