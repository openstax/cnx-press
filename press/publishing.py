import tempfile
from pathlib import Path

from pyramid.threadlocal import get_current_registry


__all__ = (
    'persist_file_to_filesystem',
)


def persist_file_to_filesystem(file):
    """Persist the given ``file`` to the filesystem within
    the shared directory space. Returns a filepath (a ``pathlib.Path``).

    """
    shared_directory = get_current_registry().settings['shared_directory']
    _, filepath = tempfile.mkstemp(dir=shared_directory)
    filepath = Path(filepath)
    with filepath.open('wb') as fb:
        fb.write(file.read())
    file.seek(0)
    return filepath
