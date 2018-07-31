import pretend

from press.events import LegacyPublicationFinished
from press.outofband import make_request
from press.subscribers.legacy_update_latest import (
    legacy_update_latest,
)


class TestLegacyUpdateLatest:

    def test(self, stub_request):
        # Create an event with a stub request
        ids = [
            ('m12345', (2, None)),
            ('m54321', (4, None)),
            ('col32154', (5, 1)),
        ]
        event = LegacyPublicationFinished(ids, stub_request)

        # Call the subcriber
        legacy_update_latest(event)

        # Check for task calls
        task_path = '.'.join([make_request.__module__, make_request.__name__])
        task = stub_request.registry.celery_app.tasks[task_path]
        expected_calls = [
            pretend.call('mock://legacy.example.org/content/col32154/latest'),
            pretend.call('mock://legacy.example.org/content/m12345/latest'),
            pretend.call('mock://legacy.example.org/content/m54321/latest'),
        ]
        assert task.delay.calls == expected_calls

        # Check for logging
        assert len(stub_request.log.info.calls) == len(ids)
        for i, (id, ver) in enumerate(sorted(ids)):
            assert id in stub_request.log.info.calls[i].args[0]
