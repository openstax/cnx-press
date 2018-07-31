from press.outofband import make_request
from press.utils import convert_to_legacy_domain


URL_TMPLT = ('{base_url}/content/{module_id}/latest')


# subscriber for press.events.LegacyPublicationFinished
def legacy_update_latest(event):
    logger = event.request.log

    # Build the legacy domain from the current request domain.
    domain = convert_to_legacy_domain(event.request.domain)
    # Build the latest content url
    scheme = event.request.scheme
    base_url = '{}://{}'.format(scheme, domain)

    # Get the celery task object
    task_path = '.'.join([make_request.__module__, make_request.__name__])
    _make_request = event.request.registry.celery_app.tasks[task_path]

    ids = sorted(event.ids)
    for id, _ in ids:
        logger.info(
            "async request made to poke '{}/latest' on the legacy system"
            .format(id)
        )
        url = URL_TMPLT.format(
            base_url=base_url,
            module_id=id,
        )
        _make_request.delay(url)
