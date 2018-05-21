import json
from pathlib import Path

import pretend
import pytest
from pyramid.events import ApplicationCreated

from press.events import LegacyPublicationFinished
from press.subscribers.track_pubs import (
    TRACKED_PUBS_DIR,
    create_tracked_pubs_location,
    get_tracked_pubs_location,
    track_publications_to_filesystem,
)


def test_get_tracked_pubs_location(monkeypatch):
    path = Path('/foo')
    get_var_location = pretend.call_recorder(lambda registry: path)
    monkeypatch.setattr(
        'press.subscribers.track_pubs.get_var_location',
        get_var_location,
    )
    registry = pretend.stub()

    loc = get_tracked_pubs_location(registry)
    assert loc == path / TRACKED_PUBS_DIR
    assert get_var_location.calls == [
        pretend.call(registry),
    ]


class TestCreateTrackedPubsLocation:

    @pytest.fixture(autouse=True)
    def setup(self, tmpdir):
        self.shared_dir = Path(tmpdir.mkdir('shared'))
        settings = {'shared_directory': self.shared_dir}
        registry = pretend.stub(settings=settings)
        self.app = pretend.stub(registry=registry)

    def test(self):
        event = ApplicationCreated(self.app)
        create_tracked_pubs_location(event)

        expected_location = self.shared_dir / TRACKED_PUBS_DIR
        assert expected_location.exists()

    def test_exists(self):
        # Create the directory
        expected_location = self.shared_dir / TRACKED_PUBS_DIR
        expected_location.mkdir()

        # test this doesn't error...
        event = ApplicationCreated(self.app)
        create_tracked_pubs_location(event)
        assert expected_location.exists()


def test_track_publications_to_filesystem(tmpdir, monkeypatch):
    shared_dir = Path(tmpdir.mkdir('shared'))
    # Note this directory is created at application startup
    (shared_dir / TRACKED_PUBS_DIR).mkdir()
    settings = {'shared_directory': shared_dir}
    registry = pretend.stub(settings=settings)

    # Create an event with a stub request
    ids = [
        ('m12345', (2, None)),
        ('m54321', (4, None)),
        ('col32154', (5, 1)),
    ]
    request = pretend.stub(registry=registry)
    event = LegacyPublicationFinished(ids, request)

    # stub the datetime.now()
    datetime = pretend.stub(now=lambda: 'now')
    monkeypatch.setattr(
        'press.subscribers.track_pubs.datetime',
        datetime,
    )

    # Call the subcriber
    track_publications_to_filesystem(event)

    # Check for a file
    with (shared_dir / TRACKED_PUBS_DIR / 'now.json').open('r') as fb:
        # ... because json converts tuples to lists
        json_formatted_ids = [[x[0], list(x[1])] for x in ids]
        assert json.load(fb) == json_formatted_ids
