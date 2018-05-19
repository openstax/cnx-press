import pretend

from press import events
from press import subscribers
from press.subscribers import legacy_enqueue


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
    ]
