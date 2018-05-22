import pretend
import requests
import requests_mock as rmock

from press.events import LegacyPublicationFinished

from press.subscribers.purge_cache import (
    _build_legacy_domain,
    purge_cache,
)


class TestBuildLegacyDomain:

    def test_prod_domain(self):
        domain = 'example.com'
        assert _build_legacy_domain(domain) == '.'.join(['legacy', domain])

    def test_dev_domain(self):
        domain = 'dev.example.com'
        assert _build_legacy_domain(domain) == '-'.join(['legacy', domain])


class TestPurgeCache:

    def test(self, requests_mock):
        request_callback = pretend.call_recorder(
            lambda request, context: 'purged')
        # mock the request to purge
        requests_mock.register_uri(
            'PURGE_REGEXP',
            rmock.ANY,
            text=request_callback,
        )

        # stub out the logger
        logger_info = pretend.call_recorder(lambda *a, **kw: None)
        logger_debug = pretend.call_recorder(lambda *a, **kw: None)
        logger = pretend.stub(info=logger_info, debug=logger_debug)
        # Create an event with a stub request
        ids = [
            ('m12345', (2, None)),
            ('m54321', (4, None)),
            ('col32154', (5, 1)),
        ]
        request = pretend.stub(
            domain='example.org',
            scheme='mock',
            log=logger,
        )
        event = LegacyPublicationFinished(ids, request)

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
        assert logger_debug.calls == [
            pretend.call("purge url:  {}".format(url)),
        ]
        assert logger_info.calls == [
            pretend.call("purged urls for the 'latest' version of '{}' "
                         "on the legacy domain"
                         .format(', '.join(map(lambda x: x[0], ids)))),
        ]

    def test_failed_request(self, requests_mock):
        # mock the failing request to purge
        requests_mock.register_uri(
            'PURGE_REGEXP',
            rmock.ANY,
            exc=requests.exceptions.ConnectTimeout,
        )

        # stub out the raven client
        captureException = pretend.call_recorder(lambda: None)
        raven_client = pretend.stub(captureException=captureException)
        # stub out the logger
        logger_info = pretend.call_recorder(lambda *a, **kw: None)
        logger_debug = pretend.call_recorder(lambda *a, **kw: None)
        logger_exception = pretend.call_recorder(lambda *a, **kw: None)
        logger = pretend.stub(
            info=logger_info,
            debug=logger_debug,
            exception=logger_exception,
        )
        # Create an event with a stub request
        ids = [
            ('m12345', (2, None)),
            ('m54321', (4, None)),
            ('col32154', (5, 1)),
        ]
        request = pretend.stub(
            domain='example.org',
            scheme='mock',
            log=logger,
            raven_client=raven_client,
        )
        event = LegacyPublicationFinished(ids, request)

        # Call the subcriber
        purge_cache(event)

        # Check raven was used...
        assert captureException.calls

        known_base_url = 'mock://legacy.example.org'
        url = (
            '{}/content/({})/latest.*$'
            .format(known_base_url, '|'.join([x[0] for x in ids]))
        )
        # Check for logging
        assert logger_debug.calls == []
        assert logger_info.calls == []
        assert logger_exception.calls == [
            pretend.call('problem purging with {}'.format(url)),
        ]
