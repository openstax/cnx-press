import json
from datetime import datetime

from press.publishing import get_var_location


TRACKED_PUBS_DIR = 'tracked-pubs'


def get_tracked_pubs_location(registry):
    return get_var_location(registry) / TRACKED_PUBS_DIR


# subscriber for pyramid.events.ApplicationCreated
def create_tracked_pubs_location(event):
    """Create the publication tracking directory"""
    get_tracked_pubs_location(event.app.registry).mkdir(exist_ok=True)


# subscriber for press.events.LegacyPublicationFinished
def track_publications_to_filesystem(event):
    """Track each publication as a file entry"""
    # This is temporary (21-May-2018) to track what publications
    # this application has made. The data may later be used
    # if we decide or need to enable "republishing" of shared content.
    directory = get_tracked_pubs_location(event.request.registry)
    filename = '{}.json'.format(str(datetime.now()))
    with (directory / filename).open('w') as fb:
        json.dump(list(event.ids), fb)
