# -*- coding: utf-8 -*-
import pytest
from webtest import TestApp


@pytest.fixture
def webapp():
    """Creates a WebTest application for functional testing."""
    from press.main import make_app
    app = make_app()
    return TestApp(app)


def test_successful_ping(webapp):
    resp = webapp.get('/ping')
    assert resp.status_code == 200
    assert b'pong' in resp.body
