import pretend

from press.events import LegacyPublicationFinished

from press.outofband import make_request
from press.subscribers.purge_cache import (
    ID_CHUNK_SIZE,
    purge_cache,
)


def _make_url(ids):
    ids = '|'.join(ids)
    known_base_url = 'mock://legacy.example.org'
    return (
        '{}/content/({})/latest.*$'
        .format(known_base_url, ids)
    )


def _chunk_ids(ids):
    start = 0
    range_stop = len(ids) + ID_CHUNK_SIZE
    for end in range(ID_CHUNK_SIZE, range_stop, ID_CHUNK_SIZE):
        yield ids[start:end]
        start = end


class TestPurgeCache:

    def test(self, stub_request):
        # Create an event with a stub request
        ids = [
            ('m12345', (2, None)),
            ('m54321', (4, None)),
            ('col32154', (5, 1)),
        ]
        event = LegacyPublicationFinished(ids, stub_request)
        url = _make_url([x[0] for x in ids])

        # Call the subcriber
        purge_cache(event)

        # Check for task calls
        task_path = '.'.join([make_request.__module__, make_request.__name__])
        task = stub_request.registry.celery_app.tasks[task_path]
        expected_calls = [
            pretend.call(url, method='PURGE_REGEXP'),
        ]
        assert task.delay.calls == expected_calls

        # Check for logging
        assert stub_request.log.debug.calls == [
            pretend.call("purge url:  {}".format(url)),
        ]
        assert stub_request.log.info.calls == [
            pretend.call("purged urls for the 'latest' version of '{}' "
                         "on the legacy domain"
                         .format(', '.join(map(lambda x: x[0], ids)))),
        ]

    def test_large_publication(self, stub_request):
        # Create an event with a stub request
        ids = [
            ('m12', (2, None)),
            ('m54', (4, None)),
            ('m22', (2, None)),
            ('m64', (4, None)),
            ('m32', (2, None)),
            ('m74', (4, None)),
            ('m42', (2, None)),
            ('m84', (4, None)),
            ('m52', (2, None)),
            ('m94', (4, None)),
            ('m62', (2, None)),
            ('m14', (4, None)),
            ('m72', (2, None)),
            ('m24', (4, None)),
            ('m82', (2, None)),
            ('m34', (4, None)),
            ('m92', (2, None)),
            ('m44', (4, None)),
            ('col32', (5, 1)),
            ('col42', (5, 1)),
            ('col52', (5, 1)),
            ('col21', (5, 1)),
            ('col52', (5, 1)),
        ]
        event = LegacyPublicationFinished(ids, stub_request)

        # Call the subcriber
        purge_cache(event)

        # Check for logging, but not the details, because that's not the
        # focus of this particular test.
        assert len(stub_request.log.debug.calls) == 3
        assert len(stub_request.log.info.calls) == 3

        # Assemble the expected urls together
        just_ids = list(map(lambda x: x[0], ids))
        expected_method = 'PURGE_REGEXP'
        expected_calls = []
        for chunk_of_ids in _chunk_ids(just_ids):
            url = _make_url(chunk_of_ids)
            expected_calls.append(pretend.call(url, method=expected_method))

        # Check for task calls
        task_path = '.'.join([make_request.__module__, make_request.__name__])
        task = stub_request.registry.celery_app.tasks[task_path]
        assert task.delay.calls == expected_calls
