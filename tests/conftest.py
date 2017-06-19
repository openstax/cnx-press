import os
import shutil
import tempfile

import pytest
from pyramid.settings import asbool
from webtest import TestApp


def _maybe_set(env_var, value):
    """Only set the env_var if it doesn't already contain a value."""
    os.environ.setdefault(env_var, value)


@pytest.fixture(scope='session')
def env_vars():
    """Set up the applications environment variables."""
    shared_directory = tempfile.mkdtemp('shared')
    _maybe_set('SHARED_DIR', shared_directory)

    yield os.environ

    # Set ``KEEP_SHARED_DIR=1`` keep the tests "shared directory".
    if not asbool(os.environ.get('KEEP_SHARED_DIR', False)):
        shutil.rmtree(shared_directory)


@pytest.fixture
def webapp(env_vars):
    """Creates a WebTest application for functional testing."""
    from press.main import make_wsgi_app
    app = make_wsgi_app()
    return TestApp(app)
