
def test_successful_ping(webapp):
    resp = webapp.get('/ping')
    assert resp.status_code == 200
    assert b'pong' in resp.body


def test_authenticated_ping_denied(webapp):
    resp = webapp.get('/auth-ping')
    assert resp.status_code == 401


def test_authenticated_ping_success(webapp):
    webapp.authorization = ('Basic', ('user1', 'password'))
    resp = webapp.get('/auth-ping')
    assert resp.status_code == 200
    assert b'pong' in resp.body
