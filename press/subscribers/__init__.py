from press import events

from .legacy_enqueue import legacy_enqueue as _legacy_enqueue


def includeme(config):
    config.add_subscriber(_legacy_enqueue, events.LegacyPublicationFinished)
