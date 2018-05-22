import requests


def _build_legacy_domain(domain):
    """Given the existing domain, translate it to the legacy domain."""
    sep = len(domain.split('.')) > 2 and '-' or '.'
    return 'legacy{}{}'.format(sep, domain)


# subscriber for press.events.LegacyPublicationFinished
def purge_cache(event):
    logger = event.request.log
    just_ids = list(map(lambda x: x[0], event.ids))

    # Build the legacy domain from the current request domain.
    domain = _build_legacy_domain(event.request.domain)

    # Build the purge url
    scheme = event.request.scheme
    base_url = '{}://{}'.format(scheme, domain)
    regex_ids = '({})'.format('|'.join(just_ids))
    url = '{}/content/{}/latest.*$'.format(base_url, regex_ids)

    purge_req = requests.Request('PURGE_REGEXP', url)
    purge_req = purge_req.prepare()
    timeout = (1, 5)  # (<connect>, <read>)
    with requests.Session() as session:
        try:
            session.send(purge_req, timeout=timeout)
        except requests.exceptions.RequestException:
            event.request.raven_client.captureException()
            logger.exception("problem purging with {}".format(url))
        else:
            logger.debug("purge url:  {}".format(url))
            logger.info("purged urls for the 'latest' version of '{}' "
                        "on the legacy domain"
                        .format(', '.join(just_ids)))
