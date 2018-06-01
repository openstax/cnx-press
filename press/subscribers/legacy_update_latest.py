import requests

from press.utils import convert_to_legacy_domain


# subscriber for press.events.LegacyPublicationFinished
def legacy_update_latest(event):
    logger = event.request.log

    # Build the legacy domain from the current request domain.
    domain = convert_to_legacy_domain(event.request.domain)
    # Build the latest content url
    scheme = event.request.scheme
    base_url = '{}://{}'.format(scheme, domain)
    url_tmplt = ('{base_url}/content/{module_id}/latest')

    timeout = (1, 120)  # (<connect>, <read>)
    ids = sorted(event.ids)
    with requests.Session() as session:
        for id, _ in ids:
            url = url_tmplt.format(
                base_url=base_url,
                module_id=id,
            )
            try:
                session.get(url, timeout=timeout)
            except requests.exceptions.RequestException:
                event.request.raven_client.captureException()
                # try one more time
                try:
                    session.get(url, timeout=timeout)
                except requests.exceptions.RequestException:
                    event.request.raven_client.captureException()
                    logger.exception("problem fetching '{}'".format(id))
                    continue
                continue
            logger.info("fetched '{}/latest' within the legacy system"
                        .format(id))
