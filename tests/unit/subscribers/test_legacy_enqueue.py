import pretend
import requests
import requests_mock as rmock

from press.events import LegacyPublicationFinished
from press.subscribers.legacy_enqueue import legacy_enqueue

from tests.helpers import (
    retryable_timeout_request_mock_callback
)


def test(requests_mock, stub_request):
    request_callback = pretend.call_recorder(
        lambda request, context: 'enqueued')
    # mock the request to enqueue
    requests_mock.register_uri('GET', rmock.ANY, text=request_callback)

    # Create an event with a stub request
    ids = [
        ('m12345', (2, None)),
        ('m54321', (4, None)),
        ('col32154', (5, 1)),
    ]
    event = LegacyPublicationFinished(ids, stub_request)

    # Call the subcriber
    legacy_enqueue(event)

    # Check for request calls
    assert len(request_callback.calls) == len(ids)
    known_base_url = 'mock://legacy.example.org'
    for i, (id, ver) in enumerate(sorted(ids)):
        url = (
            '{}/content/{}/{}/enqueue?colcomplete=True&collxml=True'
            .format(known_base_url, id, '1.{}'.format(ver[0]))
        )
        request, context = request_callback.calls[i].args
        assert url == request.url

    # Check for logging
    assert len(stub_request.log.info.calls) == len(ids)
    for i, (id, ver) in enumerate(sorted(ids)):
        assert id in stub_request.log.info.calls[i].args[0]


def test_failed_request_and_retry_failed(requests_mock, stub_request):
    ids = [
        ('m12345', (2, None)),
        ('m54321', (4, None)),
        ('col32154', (5, 1)),
    ]

    def request_callback(request, context):
        if ids[1][0] in request.url:
            raise requests.exceptions.ConnectTimeout
        else:
            return 'enqueued'

    # mock a problem request to enqueue
    requests_mock.register_uri('GET', rmock.ANY, text=request_callback)

    event = LegacyPublicationFinished(ids, stub_request)

    # Call the subcriber
    legacy_enqueue(event)

    # Check raven was used...
    assert stub_request.raven_client.captureException.calls

    # Check for logging
    assert stub_request.log.exception.calls == [
        pretend.call("problem enqueuing '{}'".format(ids[1][0])),
    ]
    assert len(stub_request.log.info.calls) == len(ids) - 1
    for i, (id, ver) in enumerate(sorted(ids)[:-1]):
        assert id in stub_request.log.info.calls[i].args[0]


def test_failed_request_and_retry_success(requests_mock, stub_request):
    ids = [
        ('m12345', (2, None)),
        ('m54321', (4, None)),
        ('col32154', (5, 1)),
    ]

    @retryable_timeout_request_mock_callback
    def request_callback(request, context, tries):
        # fails at first but succeeds on the second try
        if ids[1][0] in request.url and tries < 2:
            raise requests.exceptions.ConnectTimeout
        return 'enqueued'

    # mock a problem request to enqueue
    requests_mock.register_uri('GET', rmock.ANY, text=request_callback)

    event = LegacyPublicationFinished(ids, stub_request)

    # Call the subcriber
    legacy_enqueue(event)

    # Check raven was used...
    assert stub_request.raven_client.captureException.calls

    # Check for logging
    assert stub_request.log.exception.calls == []
