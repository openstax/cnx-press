from press.outofband import make_request
from press.utils import convert_to_legacy_domain


# Range of the sequence of ids to put into a purge url
ID_CHUNK_SIZE = 10


def _gen_purge_url(base, ids):
    """Given the base url (scheme and domain) and a sequence of ids
    (e.g. col11629, m45111), generate a purge url.

    """
    regex_ids = '({})'.format('|'.join(ids))
    return '{}/content/{}/latest.*$'.format(base, regex_ids)


# subscriber for press.events.LegacyPublicationFinished
def purge_cache(event):
    logger = event.request.log
    just_ids = list(map(lambda x: x[0], event.ids))

    # Get the celery task object
    task_path = '.'.join([make_request.__module__, make_request.__name__])
    _make_request = event.request.registry.celery_app.tasks[task_path]

    # Build the legacy domain from the current request domain.
    domain = convert_to_legacy_domain(event.request.domain)
    # Build the base part of the purge url
    scheme = event.request.scheme
    base_url = '{}://{}'.format(scheme, domain)

    start = 0
    range_stop = len(just_ids) + ID_CHUNK_SIZE
    for end in range(ID_CHUNK_SIZE, range_stop, ID_CHUNK_SIZE):
        ids = just_ids[start:end]
        url = _gen_purge_url(base_url, ids)
        _make_request.delay(url, method='PURGE_REGEXP')

        logger.debug("purge url:  {}".format(url))
        logger.info(
            "purged urls for the 'latest' version of '{}' "
            "on the legacy domain"
            .format(', '.join(ids))
        )
        # Set up for the next iterative chunk of data
        start = end
