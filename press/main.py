from .config import configure


def make_wsgi_app(config=None):  # pragma: no cover
    """WSGI application factory

    :param config: optional configuration object
    :type config: :class:`pyramid.configuration.Configurator`

    """
    if config is None:
        config = configure()
    return config.make_wsgi_app()
