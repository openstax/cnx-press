import pretend
import pytest
from pyramid import tweens

from press import raven


class TestException(Exception):
    """Used to invoke an exception within a request handler"""


def test_tween_without_error(monkeypatch):
    # Stub out the raven.Client calls
    capture_exception = pretend.call_recorder(lambda: None)
    context_clear = pretend.call_recorder(lambda: None)
    client = pretend.stub(
        captureException=capture_exception,
        context=pretend.stub(clear=context_clear),
    )
    client_factory = pretend.call_recorder(lambda dsn: client)
    monkeypatch.setattr(raven.raven, 'Client', client_factory)

    # Stub out the calls to the registry
    test_dsn = '<dsn>'
    registry = pretend.stub(settings={'sentry.dsn': test_dsn})

    @pretend.call_recorder
    def handler(request):
        pass

    tween = raven.raven_tween_factory(handler, registry)

    request = object()  # marker object
    tween(request)

    assert client_factory.calls == [pretend.call(test_dsn)]
    assert capture_exception.calls == []
    assert handler.calls == [pretend.call(request)]
    assert context_clear.calls == [pretend.call()]


def test_tween_with_error(monkeypatch):
    # Stub out the raven.Client calls
    capture_exception = pretend.call_recorder(lambda: None)
    context_clear = pretend.call_recorder(lambda: None)
    client = pretend.stub(
        captureException=capture_exception,
        context=pretend.stub(clear=context_clear),
    )
    client_factory = pretend.call_recorder(lambda dsn: client)
    monkeypatch.setattr(raven.raven, 'Client', client_factory)

    # Stub out the calls to the registry
    test_dsn = '<dsn>'
    registry = pretend.stub(settings={'sentry.dsn': test_dsn})

    @pretend.call_recorder
    def handler(request):
        raise TestException

    tween = raven.raven_tween_factory(handler, registry)

    request = object()  # marker object
    with pytest.raises(TestException):
        tween(request)

    assert client_factory.calls == [pretend.call(test_dsn)]
    assert capture_exception.calls == [pretend.call()]
    assert handler.calls == [pretend.call(request)]
    assert context_clear.calls == [pretend.call()]


def test_includeme():
    # FIXME Need to do under and over
    add_tween = pretend.call_recorder(lambda factory, over, under: None)
    config = pretend.stub(add_tween=add_tween)

    # Call the target includeme
    raven.includeme(config)

    assert config.add_tween.calls == [
        pretend.call(
            'press.raven.raven_tween_factory',
            under=tweens.INGRESS,
            over=tweens.EXCVIEW,
        ),
    ]
