import io
from pathlib import Path
from zipfile import ZipFile

from pyramid import testing as pyramid_testing

from press.publishing import (
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
