import pretend
import pytest


@pytest.fixture
def event_request(pretend_logger):
    # Stub out the raven client
    captureException = pretend.call_recorder(lambda: None)
    raven_client = pretend.stub(captureException=captureException)
    # Create an event with a stub request
    request = pretend.stub(
        domain='example.org',
        scheme='mock',
        log=pretend_logger,
        raven_client=raven_client,
    )
    return request
