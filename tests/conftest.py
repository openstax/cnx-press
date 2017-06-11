import pytest
from webtest import TestApp


@pytest.fixture
def webapp():
    """Creates a WebTest application for functional testing."""
    from press.main import make_app
    app = make_app()
    return TestApp(app)
