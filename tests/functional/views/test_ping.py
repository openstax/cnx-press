
def test_successful_ping(webapp):
    resp = webapp.get('/api/ping')
    assert resp.status_code == 200
    assert b'pong' in resp.body


def test_authenticated_ping_no_auth_denied(webapp):
    resp = webapp.get('/api/auth-ping', expect_errors=True)
    assert resp.status_code == 401


def test_authenticated_ping_bad_pass_auth_denied(webapp):
    resp = webapp.get('/api/auth-ping', expect_errors=True)
    webapp.authorization = ('Basic', ('user1', 'notapassword'))
    assert resp.status_code == 401


def test_authenticated_ping_bad_user_auth_denied(webapp):
    resp = webapp.get('/api/auth-ping', expect_errors=True)
    webapp.authorization = ('Basic', ('notauser', 'foobar'))
    assert resp.status_code == 401


def test_authenticated_ping_success(webapp):
    webapp.authorization = ('Basic', ('user1', 'foobar'))
    resp = webapp.get('/api/auth-ping')
    assert resp.status_code == 200
    assert b'pong' in resp.body


def test_publish_ping_success(webapp):
    webapp.authorization = ('Basic', ('user1', 'foobar'))
    resp = webapp.get('/api/publish-ping')
    assert resp.status_code == 200
    assert b'pong' in resp.body


def test_publish_ping_bad_user_auth_denied(webapp):
    resp = webapp.get('/api/publish-ping', expect_errors=True)
    webapp.authorization = ('Basic', ('notauser', 'foobar'))
    assert resp.status_code == 401
