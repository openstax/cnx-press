import io
from pathlib import Path
from zipfile import ZipFile

from pyramid import testing as pyramid_testing

from press.publishing import (
    discover_content_dir,
    expand_zip,
    persist_file_to_filesystem,
)


def test_persist_file_to_filesystem(tmpdir):
    file_content = io.BytesIO(b'foo bar baz')
    # Configure a dummy application.
    shared_directory = Path(tmpdir.mkdir('shared'))
    settings = {
        'shared_directory': str(shared_directory),
    }
    with pyramid_testing.testConfig(settings=settings):
        filepath = persist_file_to_filesystem(file_content)

    with filepath.open('rb') as fb:
        assert fb.read() == file_content.read()

    assert filepath in [fp for fp in shared_directory.iterdir()]


def test_expand_zip(app, tmpdir):
    zipfile = io.BytesIO()
    files = [
        'foo/bar.txt', 'foo/mar.txt',
        'bar/foo.txt', 'bar/moo.txt',
        'smoo.txt',
    ]
    with ZipFile(zipfile, mode='a') as zb:
        for file in files:
            zb.writestr(file, 'foobar')
    # Reset file pointer location
    zipfile.seek(0)

    with app:
        expand_path = expand_zip(zipfile)

    def deflate_path(path, root, parent=None):
        if path.is_dir():
            for x in path.iterdir():
                yield from deflate_path(x, root, path)
        else:
            yield path.relative_to(root)

    expanded_files = list([str(x)
                           for x in deflate_path(expand_path, expand_path)])
    assert sorted(expanded_files) == sorted(files)


def test_discover_content_dir(tmpdir):
    root = Path(str(tmpdir.mkdir('root')))
    dir = root / 'foo'
    dir.mkdir()

    found_dir = discover_content_dir(root)
    assert found_dir == dir


def test_discover_content_dir_with_multiple_dirs(tmpdir):
    root = Path(str(tmpdir.mkdir('root')))
    (root / 'foo').mkdir()
    (root / 'bar').mkdir()
    dir = root / 'alp'
    dir.mkdir()

    found_dir = discover_content_dir(root)
    assert found_dir == dir


def test_discover_content_dir_with_no_dirs(tmpdir):
    root = Path(str(tmpdir.mkdir('root')))
    for filename in ('foo', 'bar', 'baz'):
        with (root / filename).open('w') as fb:
            fb.write('smoo')

    found_dir = discover_content_dir(root)
    assert found_dir is None
