from pyramid import tweens
import raven


def _client_factory(registry):
    return raven.Client(registry.settings.get('sentry.dsn'))


def raven_tween_factory(handler, registry):
    """A tween factory that registers a tween
    that will capture uncaught exceptions.

    """
    client = _client_factory(registry)

    def tween(request):
        try:
            response = handler(request)
        except:  # noqa: E722
            client.captureException()
            raise  # raise to continue down the request pipeline
        finally:
            client.context.clear()
        return response

    return tween


def _create_raven_client(request):
    """Request attribute factory to give access non-critical exception
    handling code a way to report issues.

    """
    return _client_factory(request.registry)


def includeme(config):
    """Integrates Sentry's Raven client"""
    config.add_tween(
        'press.raven.raven_tween_factory',
        under=tweens.INGRESS,
        over=tweens.EXCVIEW,
    )
    config.add_request_method(
        _create_raven_client,
        name='raven_client',
        reify=True,
    )
