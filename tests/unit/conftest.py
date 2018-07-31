import pretend
import pytest


# List of known tasks
TASKS_AS_IMPORT_PATHS = [
    'press.outofband.make_request',
]


def _make_task(x):
    delay = pretend.call_recorder(lambda *a, **kw: None)
    return x, pretend.stub(delay=delay)


@pytest.fixture
def stub_request(pretend_logger):
    # Stub out the Celery app
    tasks = dict(map(_make_task, TASKS_AS_IMPORT_PATHS))
    celery_app = pretend.stub(tasks=tasks)

    # Stub out the Raven client
    captureException = pretend.call_recorder(lambda: None)
    raven_client = pretend.stub(captureException=captureException)

    # Stub out the Pyramid registry
    registry = pretend.stub(celery_app=celery_app)

    # Create an event with a stub request
    request = pretend.stub(
        domain='example.org',
        scheme='mock',
        log=pretend_logger,
        raven_client=raven_client,
        registry=registry,
    )
    return request
