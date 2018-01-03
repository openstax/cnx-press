import os
import pathlib
import shutil
import tempfile

import pytest
from pyramid.settings import asbool


def _maybe_set(env_var, value):
    """Only set the env_var if it doesn't already contain a value."""
    os.environ.setdefault(env_var, value)
    return os.environ[env_var]


@pytest.fixture(scope='session')
def keep_shared_directory():
    """Returns a True | False when based on the value of
    the ``KEEP_SHARED_DIR`` environment variable. Default is False

    """
    # This fixture isn't for reuse, but it does mean that it's
    # documented as a fixture the end-user can see via the pytest UI.
    return asbool(os.environ.get('KEEP_SHARED_DIR', False))


@pytest.fixture(scope='session')
def env_vars(keep_shared_directory):
    """Set up the applications environment variables."""
    temp_shared_directory = tempfile.mkdtemp('shared')
    shared_directory = _maybe_set('SHARED_DIR', temp_shared_directory)

    yield os.environ

    # Set ``KEEP_SHARED_DIR=1`` to keep the tests "shared directory"
    # if the shared directory isn't the temp directory.
    if not keep_shared_directory \
       and shared_directory != temp_shared_directory:
        for f in pathlib.Path(shared_directory).glob('*'):
            if f.name == '.gitkeep':
                continue
            elif f.is_dir():
                shutil.rmtree(f)
            else:
                f.unlink()
    shutil.rmtree(temp_shared_directory)
