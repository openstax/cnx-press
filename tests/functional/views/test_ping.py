
def test_successful_ping(webapp):
    resp = webapp.get('/ping')
    assert resp.status_code == 200
    assert b'pong' in resp.body
