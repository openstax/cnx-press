from pyramid import events as pyramid_events

from press import events

from .legacy_enqueue import legacy_enqueue as _legacy_enqueue
from .track_pubs import (
    create_tracked_pubs_location,
    track_publications_to_filesystem,
)


def includeme(config):
    config.add_subscriber(
        _legacy_enqueue,
        events.LegacyPublicationFinished,
    )
    config.add_subscriber(
        create_tracked_pubs_location,
        pyramid_events.ApplicationCreated,
    )
    config.add_subscriber(
        track_publications_to_filesystem,
        events.LegacyPublicationFinished,

    )
