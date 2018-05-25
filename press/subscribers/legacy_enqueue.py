import requests


# subscriber for press.events.LegacyPublicationFinished
def legacy_enqueue(event):
    logger = event.request.log

    # Build the enqueue RPC url
    domain = event.request.domain
    scheme = event.request.scheme
    base_url = '{}://{}'.format(scheme, domain)
    # The url is built specifically for collections, but works for modules,
    # because the code for modules doesn't care about the extra options.
    url_tmplt = (
        '{base_url}/content/{module_id}/{version}'
        '/enqueue?colcomplete=True&collxml=True'
    )

    timeout = (1, 20)  # (<connect>, <read>)
    ids = sorted(event.ids)
    with requests.Session() as session:
        for id, ver in ids:
            version = '1.{}'.format(ver[0])
            url = url_tmplt.format(
                base_url=base_url,
                module_id=id,
                version=version,
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
                    logger.exception("problem enqueuing '{}'".format(id))
                    continue
                continue
            logger.info("enqueued '{}' within the legacy system"
                        .format(id))
