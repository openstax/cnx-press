import os.path
import warnings

from pyramid.config import Configurator
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config.settings import asbool
from sqlalchemy.exc import SAWarning
from pyramid.security import Everyone, Authenticated, Allow


import hashlib
from base64 import decodestring as decode
def check_password(pass_hash, password):
    challenge_bytes = decode(pass_hash[6:])
    digest = challenge_bytes[:20]
    salt = challenge_bytes[20:]
    hr = hashlib.sha1(password.encode('utf8'))
    hr.update(salt)
    return digest == hr.digest()

class RootFactory(object):
    """Application root object factory.
    Everything is accessed from the root, so the acls defined here
    are applied to all requests.
    """

    __acl__ = (
        (Allow, Authenticated, 'view'),
    )

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):  # pragma: no cover
        raise KeyError(key)

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


def check_credentials(username, password, request):
    """Returns a sequence of principal identifiers for the user.
    """
    _hash = b'{SSHA}Tf5uQqRItW5v4j0WDM5w3cgIwfKKATpX'
    if check_password(_hash, password):
        return [username]

def configure(settings=None):
    """Configure the :mod:`pyramid.configure.Configurator` object"""
    if settings is None:
        settings = {}

    # Discover & check settings
    discover_set(settings, 'shared_directory', 'SHARED_DIR')
    assert os.path.exists(settings['shared_directory'])  # required
    # TODO check permissions for write access

    discover_set(settings, 'sentry.dsn', 'SENTRY_DSN')
    discover_set(settings, 'celery.broker', 'AMQP_URL')

    discover_set(settings, 'debug', 'DEBUG', False, asbool)
    settings['logging.level'] = settings['debug'] and 'DEBUG' or 'INFO'

    # Create the configuration object
    config = Configurator(settings=settings, root_factory=RootFactory)
    config.include('.logging')
    config.include('.raven')
    config.include('.subscribers')
    config.include('.views')
    config.include('.tasks')
    auth_policy = BasicAuthAuthenticationPolicy(check_credentials)
    config.set_authentication_policy(auth_policy)
    config.set_authorization_policy(ACLAuthorizationPolicy())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=SAWarning)
        config.include('cnxdb.contrib.pyramid')

    config.scan(ignore=['press.celery'])
    return config


__all__ = ('configure',)
