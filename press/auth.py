import hashlib
from base64 import decodestring as decode
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Allow, Authenticated


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


def check_credentials(username, password, request):
    """Returns a sequence of principal identifiers for the user.
    """
    # FIXME: fetch (maintainer) credentials from legacy DB
    _hash = b'{SSHA}Tf5uQqRItW5v4j0WDM5w3cgIwfKKATpX'
    if check_password(_hash, password):
        return [username]


def check_password(pass_hash, password):
    challenge_bytes = decode(pass_hash[6:])
    digest = challenge_bytes[:20]
    salt = challenge_bytes[20:]
    hr = hashlib.sha1(password.encode('utf8'))
    hr.update(salt)
    return digest == hr.digest()


def includeme(config):
    auth_policy = BasicAuthAuthenticationPolicy(check_credentials)
    config.set_authentication_policy(auth_policy)
    config.set_authorization_policy(ACLAuthorizationPolicy())
