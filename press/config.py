import os.path
import warnings

from pyramid.config import Configurator
from pyramid.config.settings import asbool
from sqlalchemy.exc import SAWarning


def discover_set(settings, setting_name, env_var, default=None,
                 modifier=None):
    """Discover a setting from environment variables and add it
    to the settings dictionary. A ``default`` value can be supplied
    and used when the environment variable can not be found.

    :param settings: the settings dictionary to modify
    :type settings: dict
    :param setting_name: the name of the setting to set
    :type: setting_name: str
    :param env_var: the environment variable name
    :type env_var: str
    :param default: default value to give the setting when the environment
                    variable is not set and the setting is already empty
    :param modifier: a callable used to modify the value (e.g. type cast)
    :type modifier: callable
    :returns: None

    """
    if env_var in os.environ:
        value = os.environ[env_var]
        if callable(modifier):
            value = modifier(value)
        settings[setting_name] = value
    elif default is not None:
        settings.setdefault(setting_name, default)


def configure(settings=None):
    """Configure the :mod:`pyramid.configure.Configurator` object"""
    if settings is None:
        settings = {}

    # Discover & check settings
    discover_set(settings, 'shared_directory', 'SHARED_DIR')
    assert os.path.exists(settings['shared_directory'])  # required
    # TODO check permissions for write access

    discover_set(settings, 'sentry.dsn', 'SENTRY_DSN')

    discover_set(settings, 'debug', 'DEBUG', False, asbool)
    settings['logging.level'] = settings['debug'] and 'DEBUG' or 'INFO'

    # Create the configuration object
    config = Configurator(settings=settings)
    config.include('.logging')
    config.include('.raven')
    config.include('.subscribers')
    config.include('.views')

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=SAWarning)
        config.include('cnxdb.contrib.pyramid')

    config.scan()
    return config


__all__ = ('configure',)
