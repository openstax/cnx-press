import pretend

from press.events import LegacyPublicationFinished
from press.outofband import make_request
from press.subscribers.legacy_enqueue import legacy_enqueue


def _make_url(info):
    id, ver = info
    known_base_url = 'mock://legacy.example.org'
    return (
        '{}/content/{}/{}/enqueue?colcomplete=True&collxml=True'
        .format(known_base_url, id, '1.{}'.format(ver[0]))
    )


def test(requests_mock, stub_request):

    # Create an event with a stub request
    ids = [
        ('m12345', (2, None)),
        ('m54321', (4, None)),
        ('col32154', (5, 1)),
    ]
    event = LegacyPublicationFinished(ids, stub_request)

    # Call the subcriber
    legacy_enqueue(event)

    # Check for task calls
    task_path = '.'.join([make_request.__module__, make_request.__name__])
    task = stub_request.registry.celery_app.tasks[task_path]
    expected_calls = list(map(pretend.call, map(_make_url, sorted(ids))))
    assert task.delay.calls == expected_calls

    # Check for logging
    assert len(stub_request.log.info.calls) == len(ids)
    for i, (id, ver) in enumerate(sorted(ids)):
        assert id in stub_request.log.info.calls[i].args[0]
