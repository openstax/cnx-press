from .config import configure


def make_wsgi_app(config=None):  # pragma: no cover
    """WSGI application factory"""
    if config is None:
        config = configure()
    return config.make_wsgi_app()
