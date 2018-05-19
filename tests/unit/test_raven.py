import pretend
import pytest
from pyramid import tweens

from press import raven as press_raven


class FauxException(Exception):
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
    monkeypatch.setattr(press_raven.raven, 'Client', client_factory)

    # Stub out the calls to the registry
    test_dsn = '<dsn>'
    registry = pretend.stub(settings={'sentry.dsn': test_dsn})

    @pretend.call_recorder
    def handler(request):
        pass

    tween = press_raven.raven_tween_factory(handler, registry)

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
    monkeypatch.setattr(press_raven.raven, 'Client', client_factory)

    # Stub out the calls to the registry
    test_dsn = '<dsn>'
    registry = pretend.stub(settings={'sentry.dsn': test_dsn})

    @pretend.call_recorder
    def handler(request):
        raise FauxException

    tween = press_raven.raven_tween_factory(handler, registry)

    request = object()  # marker object
    with pytest.raises(FauxException):
        tween(request)

    assert client_factory.calls == [pretend.call(test_dsn)]
    assert capture_exception.calls == [pretend.call()]
    assert handler.calls == [pretend.call(request)]
    assert context_clear.calls == [pretend.call()]


def test_includeme():
    # FIXME Need to do under and over
    add_tween = pretend.call_recorder(lambda factory, over, under: None)
    add_request_method = pretend.call_recorder(lambda fn, name, reify: None)
    config = pretend.stub(
        add_tween=add_tween,
        add_request_method=add_request_method,
    )

    # Call the target includeme
    press_raven.includeme(config)

    # Ensure the tween was registered
    assert config.add_tween.calls == [
        pretend.call(
            'press.raven.raven_tween_factory',
            under=tweens.INGRESS,
            over=tweens.EXCVIEW,
        ),
    ]

    # Ensure the raven_client request attribute was registered
    assert config.add_request_method.calls == [
        pretend.call(
            press_raven._create_raven_client,
            name='raven_client',
            reify=True,
        ),
    ]
