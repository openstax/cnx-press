import requests

from press.tasks import task
from press.utils import convert_to_legacy_domain


TIMEOUT = (1, 120)  # (<connect>, <read>)
URL_TMPLT = ('{base_url}/content/{module_id}/latest')


@task(bind=True, max_retries=3, default_retry_delay=5)
def poke_latest(self, url):
    with requests.Session() as session:
        try:
            session.get(url, timeout=TIMEOUT)
        except requests.exceptions.RequestException as exc:
            pyramid_request = self.get_pyramid_request()
            try:
                self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                # max_retries will stop us from doing a too many retries.
                pyramid_request.raven_client.captureException()
                raise
            pyramid_request.log.exception("problem fetching '{}'".format(url))


# subscriber for press.events.LegacyPublicationFinished
def legacy_update_latest(event):
    logger = event.request.log

    # Build the legacy domain from the current request domain.
    domain = convert_to_legacy_domain(event.request.domain)
    # Build the latest content url
    scheme = event.request.scheme
    base_url = '{}://{}'.format(scheme, domain)

    # Get the celery task object
    task_name = 'press.subscribers.legacy_update_latest.poke_latest'
    poke_latest = event.request.registry.celery_app.tasks[task_name]

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
        poke_latest.delay(url)
