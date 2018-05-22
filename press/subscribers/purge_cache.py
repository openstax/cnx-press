import requests


# Range of the sequence of ids to put into a purge url
ID_CHUNK_SIZE = 10
# Used by the quest
TIMEOUT = (1, 5)  # (<connect>, <read>)


def _build_legacy_domain(domain):
    """Given the existing domain, translate it to the legacy domain."""
    sep = len(domain.split('.')) > 2 and '-' or '.'
    return 'legacy{}{}'.format(sep, domain)


def _gen_purge_url(base, ids):
    """Given the base url (scheme and domain) and a sequence of ids
    (e.g. col11629, m45111), generate a purge url.

    """
    regex_ids = '({})'.format('|'.join(ids))
    return '{}/content/{}/latest.*$'.format(base, regex_ids)


def _make_request(url):
    """requests.Request factory for creating a purge request"""
    purge_req = requests.Request('PURGE_REGEXP', url)
    return purge_req.prepare()


# subscriber for press.events.LegacyPublicationFinished
def purge_cache(event):
    logger = event.request.log
    just_ids = list(map(lambda x: x[0], event.ids))

    # Build the legacy domain from the current request domain.
    domain = _build_legacy_domain(event.request.domain)
    # Build the base part of the purge url
    scheme = event.request.scheme
    base_url = '{}://{}'.format(scheme, domain)

    with requests.Session() as session:
        start = 0
        range_stop = len(just_ids) + ID_CHUNK_SIZE
        for end in range(ID_CHUNK_SIZE, range_stop, ID_CHUNK_SIZE):
            url = _gen_purge_url(base_url, just_ids[start:end])
            req = _make_request(url)
            try:
                session.send(req, timeout=TIMEOUT)
            except requests.exceptions.RequestException:
                event.request.raven_client.captureException()
                logger.exception("problem purging with {}".format(url))
            else:
                logger.debug("purge url:  {}".format(url))
                logger.info("purged urls for the 'latest' version of '{}' "
                            "on the legacy domain"
                            .format(', '.join(just_ids)))
            finally:
                start = end
