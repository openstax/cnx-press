from pyramid.config import Configurator


def configure(settings=None):
    """Configure the Configurator object"""
    if settings is None:
        settings = {}

    # Apply default settings

    # Discover settings

    # Check for required settings

    # Create the configuration object
    config = Configurator(settings=settings)
    config.include('.views')

    config.scan()
    return config


__all__ = ('configure',)
