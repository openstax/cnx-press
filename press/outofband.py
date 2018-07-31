"""\
Out-of-band asynchronous task (a.k.a. Celery tasks).

"""
import requests

from press.tasks import task


REQUESTS_TIMEOUT = (1, 120)  # (<connect>, <read>)


@task(bind=True, max_retries=3, default_retry_delay=5)
def make_request(self, url):
    with requests.Session() as session:
        try:
            session.get(url, timeout=REQUESTS_TIMEOUT)
        except requests.exceptions.RequestException as exc:
            pyramid_request = self.get_pyramid_request()
            try:
                self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                # max_retries will stop us from doing a too many retries.
                pyramid_request.raven_client.captureException()
                raise
            msg = "problem requesting '{}'".format(url)
            pyramid_request.log.exception(msg)
