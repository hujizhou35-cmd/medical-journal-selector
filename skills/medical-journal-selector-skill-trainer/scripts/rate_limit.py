"""Shared, process-local request-entry pacing for parallel evidence retrieval.

The defaults (two requests per entry hostname, 0.5 seconds between starts) are
conservative local settings, not a provider's published rate-limit requirement.
The caller must hold its slot through opening, reading and closing the response.
Redirects retain urllib's behavior and existing permission checks: pacing applies
to the URL's entry hostname, not every destination in a redirect chain. Separate
processes do not share these limits.
"""
from __future__ import annotations

import math
import threading
import time
import urllib.parse
from contextlib import contextmanager


class _HostState:
    def __init__(self, max_concurrent):
        self.slots = threading.BoundedSemaphore(max_concurrent)
        self.start_lock = threading.Lock()
        self.last_started = None


class HostPacer:
    """Bound in-flight requests and space starts without blocking other hosts."""

    def __init__(self, max_concurrent=2, start_spacing=0.5, *, clock=None, sleep=None):
        if type(max_concurrent) is not int or max_concurrent < 1:
            raise ValueError('max_concurrent must be a positive integer')
        if not math.isfinite(start_spacing) or start_spacing < 0:
            raise ValueError('start_spacing must be finite and nonnegative')
        self.max_concurrent = max_concurrent
        self.start_spacing = start_spacing
        self._clock = clock or time.monotonic
        self._sleep = sleep or time.sleep
        self._hosts = {}
        self._hosts_lock = threading.Lock()

    def _state(self, url):
        host = urllib.parse.urlsplit(url).hostname
        if not host:
            raise ValueError('Request pacing requires a URL with a hostname')
        host = host.casefold().rstrip('.')
        with self._hosts_lock:
            return self._hosts.setdefault(host, _HostState(self.max_concurrent))

    @contextmanager
    def slot(self, url):
        state = self._state(url)
        with state.slots:
            with state.start_lock:
                if state.last_started is not None:
                    while True:
                        delay = state.last_started + self.start_spacing - self._clock()
                        if delay <= 0:
                            break
                        self._sleep(delay)
                state.last_started = self._clock()
            yield


SHARED_HOST_PACER = HostPacer()


def request_slot(url):
    """Use the one shared limiter across corpus APIs and official-page fetches."""
    return SHARED_HOST_PACER.slot(url)
