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
        (Allow, 'Maintainer', 'publish'),
    )

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):  # pragma: no cover
        raise KeyError(key)


def check_credentials(username, password, request):
    """Returns a sequence of principal identifiers for the user.
    """
    t = request.db_tables

    with request.get_db_engine('common').begin() as db_conn:
        result = db_conn.execute(
            t.persons.select()
            .where(t.persons.c.personid == username))
        try:
            user = result.fetchone()
            _hash = user.passwd
            if check_password(_hash, password):
                if user.groups is not None:
                    return [username] + user.groups
                else:
                    return [username]
        except AttributeError:
            pass


def check_password(pass_hash, password):
    """Check password against SSHA hashed password."""
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
