import io
from pathlib import Path

from pyramid import testing as pyramid_testing


def test_persist_file_to_filesystem(tmpdir):
    file_content = io.BytesIO(b'foo bar baz')
    # Configure a dummy application.
    shared_directory = Path(tmpdir.mkdir('shared'))
    settings = {
        'shared_directory': str(shared_directory),
    }
    with pyramid_testing.testConfig(settings=settings):
        from press.publishing import persist_file_to_filesystem
        filepath = persist_file_to_filesystem(file_content)

    with filepath.open('rb') as fb:
        assert fb.read() == file_content.read()

    assert filepath in [fp for fp in shared_directory.iterdir()]
