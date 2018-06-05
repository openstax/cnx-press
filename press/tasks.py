"""\
Implementation of the Celery framework within a Pyramid application.

Use the ``task`` decorator provided by this module where the Celery
documentation says to use ``@app.task``. It is used to register a function as
a task without making the celery application a global object.

"""
import celery
import venusian
from pyramid.scripting import prepare


class PyramidAwareTask(celery.Task):
    """A Pyramid aware version of ``celery.task.Task``.
    This sets up the pyramid application within the thread, thus allowing
    ``pyramid.threadlocal`` functions to work as expected.
    Task execution also provides a :class:``pyramid.request.Request``
    as the first argument to each task. This allows for easy access
    to the component registry.

    """
    # This is an altered version of the warehouse project's
    # warehouse/tasks.py, which enables a pyramid 'request' and
    # therefore a 'registry' to be used during task execution.

    # Note, warehouse's implementation is much better because it uses
    # the transaction manager before committing to enqueuing a task.

    @property
    def registry(self):
        return self.app.pyramid_config.registry

    def get_pyramid_request(self):
        if not hasattr(self.request, 'pyramid_env'):
            registry = self.app.pyramid_config.registry
            env = prepare(registry=registry)
            self.request.update(pyramid_env=env)

        return self.request.pyramid_env["request"]

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if hasattr(self.request, 'pyramid_env'):
            pyramid_env = self.request.pyramid_env
            pyramid_env['request']._process_finished_callbacks()
            pyramid_env['closer']()


def task(**kwargs):
    """A function task decorator used in place of ``@celery_app.task``."""

    def wrapper(wrapped):

        def callback(scanner, name, obj):
            celery_app = scanner.config.registry.celery_app
            celery_app.task(**kwargs)(obj)

        venusian.attach(wrapped, callback)
        return wrapped

    return wrapper


def _get_celery_app(config):
    """This exposes the celery app. The app is actually created as part
    of the pyramid configuration. This provides a means for using
    the celery app functional as a stand-alone celery application,
    which is how the work processes run.

    Note, the pyramid configuration is on the celery app, so that
    the registry can be used by tasks inside the
    celery worker process pool. See ``PyramidAwareTask.__call__``.

    """
    return config.registry.celery_app


def includeme(config):
    settings = config.registry.settings

    config.registry.celery_app = celery.Celery('press', autofinalize=False)

    config.registry.celery_app.conf.update(
        broker_url=settings['celery.broker'],
    )
    # Override the existing Task class.
    config.registry.celery_app.Task = PyramidAwareTask
    # Append the Pyramid configuration to the Celery app
    config.registry.celery_app.pyramid_config = config

    # Set the default celery app so that the AsyncResult class is able
    # to assume the celery backend.
    config.registry.celery_app.set_default()

    # Finalize the celery application configuration when the pyramid
    # application has been configured/committed.
    config.action(('celery', 'finalize'), config.registry.celery_app.finalize)

    config.add_directive('make_celery_app', _get_celery_app)
