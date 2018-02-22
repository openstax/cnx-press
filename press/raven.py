from pyramid import tweens
import raven


def raven_tween_factory(handler, registry):
    client = raven.Client(registry.settings.get('sentry.dsn'))

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


def includeme(config):
    """Integrates Sentry's Raven client"""
    config.add_tween(
        'press.raven.raven_tween_factory',
        under=tweens.INGRESS,
        over=tweens.EXCVIEW,
    )
