"""Thread/clock/response fixtures only; never access a provider or policy page."""
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
import broker
import corpus
import rate_limit
from rate_limit import HostPacer


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.delays = []
        self.lock = threading.Lock()

    def monotonic(self):
        with self.lock:
            return self.now

    def sleep(self, delay):
        with self.lock:
            self.delays.append(delay)
            self.now += delay


class RecordingPacer:
    def __init__(self):
        self.active = 0
        self.events = []

    @contextmanager
    def slot(self, url):
        self.active += 1
        self.events.append(('slot-enter', url))
        try:
            yield
        finally:
            self.events.append(('slot-exit', url))
            self.active -= 1


class FixtureResponse:
    def __init__(self, pacer, content=b'fixture', final_url='https://publisher.example/final',
                 mime='text/html', read_error=None):
        self.pacer, self.content, self.final_url = pacer, content, final_url
        self.read_error = read_error
        self.headers = SimpleNamespace(get_content_type=lambda: mime)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if self.pacer.active != 1:
            raise AssertionError('Host slot was released before response close')
        self.pacer.events.append(('response-close', self.final_url))

    def read(self):
        if self.pacer.active != 1:
            raise AssertionError('Host slot was released before response body read')
        self.pacer.events.append(('response-read', self.final_url))
        if self.read_error:
            raise self.read_error
        return self.content

    def geturl(self):
        return self.final_url


class HostPacerTests(unittest.TestCase):
    def test_default_start_spacing_is_shared_by_hostname_not_url(self):
        clock = FakeClock()
        pacer = HostPacer(clock=clock.monotonic, sleep=clock.sleep)
        starts = []
        for url in ('https://API.CROSSREF.ORG/works?a=1',
                    'https://api.crossref.org./journals/1234-5678',
                    'http://api.crossref.org:8080/works?a=2'):
            with pacer.slot(url):
                starts.append(clock.monotonic())
        self.assertEqual(starts, [0.0, 0.5, 1.0])
        self.assertEqual(clock.delays, [0.5, 0.5])

    def test_spacing_rechecks_clock_when_wait_returns_early(self):
        clock = FakeClock()
        interrupted = []

        def early_once(delay):
            interrupted.append(delay)
            clock.sleep(delay/2 if len(interrupted) == 1 else delay)

        pacer = HostPacer(clock=clock.monotonic, sleep=early_once)
        with pacer.slot('https://www.ebi.ac.uk/first'):
            pass
        with pacer.slot('https://www.ebi.ac.uk/second'):
            self.assertEqual(clock.monotonic(), 0.5)
        self.assertEqual(interrupted, [0.5, 0.25])

    def test_ten_parallel_requests_have_at_most_two_in_flight(self):
        clock = FakeClock()
        pacer = HostPacer(clock=clock.monotonic, sleep=clock.sleep)
        ready = threading.Barrier(11)
        two_entered, third_entered, release = threading.Event(), threading.Event(), threading.Event()
        lock = threading.Lock()
        active, maximum, count = 0, 0, 0

        def worker(index):
            nonlocal active, maximum, count
            ready.wait(timeout=5)
            with pacer.slot('https://publisher.example/policy/'+str(index)):
                with lock:
                    active += 1
                    count += 1
                    maximum = max(maximum, active)
                    if count == 2:
                        two_entered.set()
                    if count == 3:
                        third_entered.set()
                if not release.wait(timeout=5):
                    raise AssertionError('Synthetic response release timed out')
                with lock:
                    active -= 1

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(worker, i) for i in range(10)]
            try:
                ready.wait(timeout=5)
                self.assertTrue(two_entered.wait(timeout=5))
                self.assertFalse(third_entered.wait(timeout=0.05))
            finally:
                release.set()
            for future in futures:
                future.result(timeout=5)
        self.assertEqual(count, 10)
        self.assertEqual(maximum, 2)
        self.assertEqual(active, 0)

    def test_full_or_waiting_host_does_not_block_a_different_host(self):
        clock = FakeClock()
        pacer = HostPacer(clock=clock.monotonic, sleep=clock.sleep)
        with pacer.slot('https://www.ebi.ac.uk/first'):
            with pacer.slot('https://www.ebi.ac.uk/second'):
                before = clock.monotonic()
                with pacer.slot('https://api.crossref.org/journals/1234-5678'):
                    self.assertEqual(clock.monotonic(), before)
        self.assertEqual(clock.delays, [0.5])

    def test_body_failure_releases_the_host_slot(self):
        clock = FakeClock()
        pacer = HostPacer(max_concurrent=1, clock=clock.monotonic, sleep=clock.sleep)
        with self.assertRaises(OSError):
            with pacer.slot('https://www.ebi.ac.uk/failed'):
                raise OSError('Synthetic read failure')
        with ThreadPoolExecutor(max_workers=1) as pool:
            def retry():
                with pacer.slot('https://www.ebi.ac.uk/retry'):
                    return 'retried'
            self.assertEqual(pool.submit(retry).result(timeout=2), 'retried')


class RetrievalPacingIntegrationTests(unittest.TestCase):
    def test_corpus_get_holds_shared_slot_through_read_and_close(self):
        pacer = RecordingPacer()
        response = FixtureResponse(pacer)
        url = 'https://api.crossref.org/journals/1234-5678'
        with patch('rate_limit.SHARED_HOST_PACER', pacer), \
             patch('corpus.urllib.request.urlopen', return_value=response) as opened:
            self.assertEqual(corpus.get(url, timeout=13, attempts=1), b'fixture')
        self.assertEqual(opened.call_args.kwargs['timeout'], 13)
        self.assertEqual([kind for kind, _ in pacer.events],
                         ['slot-enter', 'response-read', 'response-close', 'slot-exit'])
        self.assertEqual(pacer.active, 0)

    def test_retries_take_fresh_slots_and_keep_existing_backoff(self):
        pacer = RecordingPacer()
        responses = [FixtureResponse(pacer, read_error=OSError('fixture read failure')),
                     FixtureResponse(pacer, read_error=OSError('fixture read failure')),
                     FixtureResponse(pacer, content=b'retry worked')]
        with patch('rate_limit.SHARED_HOST_PACER', pacer), \
             patch('corpus.urllib.request.urlopen', side_effect=responses) as opened, \
             patch('corpus.time.sleep') as backoff:
            self.assertEqual(corpus.get('https://www.ebi.ac.uk/search', attempts=3), b'retry worked')
        self.assertEqual(opened.call_count, 3)
        self.assertEqual([call.args[0] for call in backoff.call_args_list], [1, 2])
        self.assertEqual(sum(kind == 'slot-enter' for kind, _ in pacer.events), 3)
        self.assertEqual(sum(kind == 'slot-exit' for kind, _ in pacer.events), 3)
        self.assertEqual(pacer.active, 0)

    def test_official_fetch_preserves_return_and_redirect_permission_handler(self):
        pacer = RecordingPacer()
        response = FixtureResponse(pacer, final_url='https://www.frontiersin.org/guidelines')
        opener = SimpleNamespace(open=lambda *args, **kwargs: response)
        entry = 'https://www.frontiersin.org/about/policies'
        with patch('rate_limit.SHARED_HOST_PACER', pacer), \
             patch('broker.urllib.request.build_opener', return_value=opener) as built:
            self.assertEqual(broker.fetch_page(entry),
                             (b'fixture', 'https://www.frontiersin.org/guidelines', 'text/html'))
        self.assertIsInstance(built.call_args.args[0], broker.OfficialRedirect)
        self.assertEqual([kind for kind, _ in pacer.events],
                         ['slot-enter', 'response-read', 'response-close', 'slot-exit'])
        self.assertEqual(pacer.events[0], ('slot-enter', entry))

    def test_official_unsupported_mime_releases_the_shared_slot(self):
        pacer = RecordingPacer()
        opener = SimpleNamespace(open=lambda *args, **kwargs: FixtureResponse(pacer, mime='application/pdf'))
        with patch('rate_limit.SHARED_HOST_PACER', pacer), \
             patch('broker.urllib.request.build_opener', return_value=opener):
            with self.assertRaisesRegex(ValueError, 'Unsupported'):
                broker.fetch_page('https://www.frontiersin.org/policy.pdf')
        self.assertEqual(pacer.active, 0)
        self.assertEqual([kind for kind, _ in pacer.events],
                         ['slot-enter', 'response-close', 'slot-exit'])

    def test_api_and_official_fetches_share_the_same_host_start_schedule(self):
        clock = FakeClock()
        pacer = HostPacer(clock=clock.monotonic, sleep=clock.sleep)
        starts = []

        class Response:
            headers = SimpleNamespace(get_content_type=lambda: 'text/plain')
            def __enter__(self): return self
            def __exit__(self, *exc): pass
            def read(self): return b'fixture'
            def geturl(self): return 'https://www.ebi.ac.uk/final'

        def open_fixture(*args, **kwargs):
            starts.append(clock.monotonic())
            return Response()

        with patch('rate_limit.SHARED_HOST_PACER', pacer), \
             patch('corpus.urllib.request.urlopen', side_effect=open_fixture), \
             patch('broker.urllib.request.build_opener', return_value=SimpleNamespace(open=open_fixture)):
            corpus.get('https://www.ebi.ac.uk/europepmc/search', attempts=1)
            broker.fetch_page('https://www.ebi.ac.uk/policy')
            corpus.get('https://api.crossref.org/journals/1234-5678', attempts=1)
        self.assertEqual(starts, [0.0, 0.5, 0.5])
        self.assertEqual(clock.delays, [0.5])


if __name__ == '__main__':
    unittest.main()
