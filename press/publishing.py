import tempfile
import zipfile
from pathlib import Path

from pyramid.threadlocal import get_current_registry


__all__ = (
    'discover_content_dir',
    'expand_zip',
    'get_var_location',
    'persist_file_to_filesystem',
)


def get_var_location(registry=None):
    """Lookup the var location for this application.

    :param registry: the application registry
    :type registry: :class:`pyramid.registry.Registry`

    """
    if registry is None:
        registry = get_current_registry()
    return Path(registry.settings['shared_directory'])


def persist_file_to_filesystem(file):
    """Persist the given ``file`` to the filesystem within
    the shared directory space.

    :param file: file to persist
    :type file: file-like object
    :return: path to written file
    :rtype: :class:`pathlib.Path`

    """
    shared_directory = get_var_location()
    _, filepath = tempfile.mkstemp(dir=str(shared_directory))
    filepath = Path(filepath)
    with filepath.open('wb') as fb:
        fb.write(file.read())
    file.seek(0)
    return filepath


def expand_zip(file):
    """Expand a zip file into a temporary directory and return the path
    to the expanded directory location.

    :param file: zip file to expand
    :type file: can be a path to a file (a string), a file-like object
                or a path-like object
    :return: path to expanded zip
    :rtype: :class:`pathlib.Path`

    """
    shared_directory = get_var_location()
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


def discover_content_dir(dir):
    """Given an expanded litezip directory path,
    discover the name of the contents directory within it.

    :param dir: directory to look in for a unknown directory name
    :type dir: :class:`pathlib.Path`
    :return: the found directory
    :rtype: :class:`pathlib.Path`

    """
    for path in dir.iterdir():
        if path.is_dir():
            return path
    return None
