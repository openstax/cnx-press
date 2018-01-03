import pytest
from pyramid import testing as pyramid_testing


@pytest.fixture
def app(env_vars):
    from press.config import configure
    yield configure()
    pyramid_testing.tearDown()
