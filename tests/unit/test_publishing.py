import io
from pathlib import Path
from zipfile import ZipFile

import pretend
import pytest
from pyramid import testing as pyramid_testing

from press.publishing import (
    discover_content_dir,
    expand_zip,
    get_var_location,
    persist_file_to_filesystem,
)


class TestGetVarLocation:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.shared_dir = '/foo'
        self.settings = {'shared_directory': self.shared_dir}
        self.registry = pretend.stub(settings=self.settings)
        func = pretend.call_recorder(lambda: self.registry)
        self.get_current_registry = func

    def test_without_params(self, monkeypatch):
        monkeypatch.setattr(
            'press.publishing.get_current_registry',
            self.get_current_registry,
        )

        loc = get_var_location()
        assert isinstance(loc, Path)
        assert str(loc) == self.shared_dir

    def test_with_params(self, monkeypatch):

        def get_current_registry(registry=None):
            raise AssertionError("shouldn't call this func")

        monkeypatch.setattr(
            'press.publishing.get_current_registry',
            get_current_registry,
        )

        loc = get_var_location(self.registry)
        assert isinstance(loc, Path)
        assert str(loc) == self.shared_dir


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


def test_discover_content_dir_with_multiple_dirs():
    # We stub out the objects here because the 'iterdir' method on
    # a Path returns a list in arbitrary order.
    dirs = []
    for name in range(0, 3):
        # Stub a Path with the 'is_dir' method.
        dirs.append(pretend.stub(is_dir=lambda: True))
    # Stub the root directory to list from
    root = pretend.stub(iterdir=lambda: dirs)

    found_dir = discover_content_dir(root)
    assert found_dir == dirs[0]


def test_discover_content_dir_with_no_dirs(tmpdir):
    root = Path(str(tmpdir.mkdir('root')))
    for filename in ('foo', 'bar', 'baz'):
        with (root / filename).open('w') as fb:
            fb.write('smoo')

    found_dir = discover_content_dir(root)
    assert found_dir is None
