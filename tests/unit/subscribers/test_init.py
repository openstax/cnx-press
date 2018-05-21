import pretend
from pyramid import events as pyramid_events

from press import events
from press import subscribers
from press.subscribers import legacy_enqueue, track_pubs


def test_includeme():
    add_subscriber = pretend.call_recorder(lambda *a, **kw: None)
    config = pretend.stub(
        add_subscriber=add_subscriber,
    )

    # Call the target includeme
    subscribers.includeme(config)

    # Ensure the enqueuing publication finished subscriber is registered
    assert add_subscriber.calls == [
        pretend.call(
            legacy_enqueue.legacy_enqueue,
            events.LegacyPublicationFinished,
        ),
        pretend.call(
            track_pubs.create_tracked_pubs_location,
            pyramid_events.ApplicationCreated,
        ),
        pretend.call(
            track_pubs.track_publications_to_filesystem,
            events.LegacyPublicationFinished,
        ),
    ]
