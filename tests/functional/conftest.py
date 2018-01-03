import pytest
from webtest import TestApp


@pytest.fixture
def webapp(env_vars):
    """Creates a WebTest application for functional testing."""
    from press.main import make_wsgi_app
    app = make_wsgi_app()
    return TestApp(app)
