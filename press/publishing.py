import tempfile
import zipfile
from pathlib import Path

from pyramid.threadlocal import get_current_registry


__all__ = (
    'expand_zip',
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


def expand_zip(file):
    """Expand a zip file into a temporary directory and return the path
    to the expanded directory location (a ``pathlib.Path``).
    ``file`` can be a path to a file (a string), a file-like object
    or a path-like object.

    """
    settings = get_current_registry().settings
    shared_directory = Path(settings['shared_directory'])
    _names = tempfile._get_candidate_names()
    while True:
        dir = shared_directory / next(_names)
        try:
            dir.mkdir()
        except FileExistsError:  # pragma: no cover
            continue
        break
    expand_path = dir

    with zipfile.ZipFile(file) as z:
        z.extractall(path=str(expand_path))
    return expand_path
