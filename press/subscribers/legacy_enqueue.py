from press.outofband import make_request
from press.utils import convert_to_legacy_domain


# The url is built specifically for collections, but works for modules,
# because the code for modules doesn't care about the extra options.
URL_TMPLT = (
    '{base_url}/content/{module_id}/{version}'
    '/enqueue?colcomplete=True&collxml=True'
)


# subscriber for press.events.LegacyPublicationFinished
def legacy_enqueue(event):
    logger = event.request.log

    # Get the celery task object
    task_path = '.'.join([make_request.__module__, make_request.__name__])
    _make_request = event.request.registry.celery_app.tasks[task_path]

    # Build the enqueue RPC url
    domain = convert_to_legacy_domain(event.request.domain)
    scheme = event.request.scheme
    base_url = '{}://{}'.format(scheme, domain)

    for id, ver in sorted(event.ids):
        version = '1.{}'.format(ver[0])
        url = URL_TMPLT.format(
            base_url=base_url,
            module_id=id,
            version=version,
        )
        _make_request.delay(url)
        logger.info(
            "asynchronously enqueued '{}' within the legacy system".format(id)
        )
