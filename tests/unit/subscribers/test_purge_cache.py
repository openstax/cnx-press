import pretend
import requests
import requests_mock as rmock

from press.events import LegacyPublicationFinished

from press.subscribers.purge_cache import (
    ID_CHUNK_SIZE,
    purge_cache,
)


class TestPurgeCache:

    def test(self, requests_mock, stub_request):
        request_callback = pretend.call_recorder(
            lambda request, context: 'purged')
        # mock the request to purge
        requests_mock.register_uri(
            'PURGE_REGEXP',
            rmock.ANY,
            text=request_callback,
        )

        # Create an event with a stub request
        ids = [
            ('m12345', (2, None)),
            ('m54321', (4, None)),
            ('col32154', (5, 1)),
        ]
        event = LegacyPublicationFinished(ids, stub_request)

        # Call the subcriber
        purge_cache(event)

        # Check for request call
        assert request_callback.calls
        known_base_url = 'mock://legacy.example.org'
        url = (
            '{}/content/({})/latest.*$'
            .format(known_base_url, '|'.join([x[0] for x in ids]))
        )
        sent_request, context = request_callback.calls[0].args
        assert url == sent_request.url

        # Check for logging
        assert stub_request.log.debug.calls == [
            pretend.call("purge url:  {}".format(url)),
        ]
        assert stub_request.log.info.calls == [
            pretend.call("purged urls for the 'latest' version of '{}' "
                         "on the legacy domain"
                         .format(', '.join(map(lambda x: x[0], ids)))),
        ]

    def test_failed_request(self, requests_mock, stub_request):
        # mock the failing request to purge
        requests_mock.register_uri(
            'PURGE_REGEXP',
            rmock.ANY,
            exc=requests.exceptions.ConnectTimeout,
        )

        # Create an event with a stub request
        ids = [
            ('m12345', (2, None)),
            ('m54321', (4, None)),
            ('col32154', (5, 1)),
        ]
        event = LegacyPublicationFinished(ids, stub_request)

        # Call the subcriber
        purge_cache(event)

        # Check raven was used...
        assert stub_request.raven_client.captureException.calls

        known_base_url = 'mock://legacy.example.org'
        url = (
            '{}/content/({})/latest.*$'
            .format(known_base_url, '|'.join([x[0] for x in ids]))
        )
        # Check for logging
        assert stub_request.log.debug.calls == []
        assert stub_request.log.info.calls == []
        assert stub_request.log.exception.calls == [
            pretend.call('problem purging with {}'.format(url)),
        ]

    def test_large_publication(self, requests_mock, stub_request):

        def _make_callback(text='purged', is_exception=False):
            def callback(request, context):
                if is_exception:
                    raise requests.exceptions.ConnectTimeout
                else:
                    return text
            return callback

        # mock the failing request to purge
        response_list = [
            _make_callback(),
            _make_callback(is_exception=True),
            _make_callback(),
        ]
        # format the responses for registration and call recording
        response_list = [
            {'text': pretend.call_recorder(y)} for y in response_list
        ]
        # register the mock request to purge
        requests_mock.register_uri(
            'PURGE_REGEXP',
            rmock.ANY,
            response_list,
        )

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

        # Check raven was used...
        assert len(stub_request.raven_client.captureException.calls) == 1

        # Check for logging, but not the details, because that's not the
        # focus of this particular test.
        assert len(stub_request.log.debug.calls) == 2
        assert len(stub_request.log.info.calls) == 2
        assert len(stub_request.log.exception.calls) == 1

        # Check the requests have the correct set of ids in them.
        just_ids = list(map(lambda x: x[0], ids))
        sent_requests = map(
            lambda x: x['text'].calls[0].args[0],
            response_list,
        )
        for i, request in enumerate(sent_requests):
            start = i * ID_CHUNK_SIZE
            end = (i + 1) * ID_CHUNK_SIZE
            expected_text = '|'.join(just_ids[start:end])
            assert expected_text in request.url
