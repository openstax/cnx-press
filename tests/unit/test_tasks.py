from unittest import mock

import pretend
import venusian
from celery import Celery

from press import tasks as press_tasks


class TestPyramidAwareTask:
    # This is an altered version of the warehouse project's
    # tests/unit/test_tasks.py.

    # Note, warehouse's implementation tests a lot more than this
    # because it uses a transaction manager to control task execution.

    @property
    def Task(self):
        return press_tasks.PyramidAwareTask

    def test_call(self, monkeypatch):
        request = pretend.stub()
        registry = pretend.stub()
        result = pretend.stub()

        prepared = {
            'registry': registry,
            'request': request,
            'closer': pretend.call_recorder(lambda: None),
        }
        prepare = pretend.call_recorder(lambda *a, **kw: prepared)
        monkeypatch.setattr(
            press_tasks,
            'prepare',
            prepare,
        )

        @pretend.call_recorder
        def runner(self):
            assert self.registry is registry
            assert self.get_pyramid_request() is request
            return result

        task = self.Task()
        task.app = Celery()
        task.app.pyramid_config = pretend.stub(registry=registry)
        task.run = runner

        # Call as if it were a bound task (i.e. `@task(bind=True)`)
        assert task(task) is result
        assert prepare.calls == [pretend.call(registry=registry)]
        assert runner.calls == [pretend.call(task)]

    def test_creates_request(self, monkeypatch):
        registry = pretend.stub()
        pyramid_env = {'request': pretend.stub()}

        monkeypatch.setattr(
            press_tasks,
            'prepare',
            lambda *a, **k: pyramid_env,
        )

        obj = self.Task()
        obj.app.pyramid_config = pretend.stub(registry=registry)

        request = obj.get_pyramid_request()

        assert obj.request.pyramid_env == pyramid_env
        assert request is pyramid_env['request']

    def test_reuses_request(self):
        pyramid_env = {'request': pretend.stub()}

        obj = self.Task()
        obj.request.update(pyramid_env=pyramid_env)

        assert obj.get_pyramid_request() is pyramid_env['request']

    def test_after_return_without_pyramid_env(self):
        obj = self.Task()
        assert (
            obj.after_return(
                pretend.stub(),
                pretend.stub(),
                pretend.stub(),
                pretend.stub(),
                pretend.stub(),
                pretend.stub(),
            )
            is None
        )

    def test_after_return_closes_env_runs_request_callbacks(self):
        obj = self.Task()
        _process_finished_callbacks = pretend.call_recorder(lambda: None)
        obj.request.pyramid_env = {
            'request': pretend.stub(
                _process_finished_callbacks=_process_finished_callbacks,
            ),
            'closer': pretend.call_recorder(lambda: None),
        }

        obj.after_return(
            pretend.stub(),
            pretend.stub(),
            pretend.stub(),
            pretend.stub(),
            pretend.stub(),
            pretend.stub(),
        )

        assert _process_finished_callbacks.calls == [pretend.call()]
        assert obj.request.pyramid_env['closer'].calls == [pretend.call()]


def test_task_decorator(monkeypatch):
    venusian_attach = pretend.call_recorder(lambda *a, **kw: None)
    monkeypatch.setattr(venusian, 'attach', venusian_attach)
    task_kwargs = dict(bind=True, relax=False)

    @press_tasks.task(**task_kwargs)
    def check():
        pass

    # Test attachment for venusian processing
    assert venusian_attach.calls == [
        pretend.call(check, mock.ANY),
    ]
    callback = venusian_attach.calls[0].args[1]

    task = pretend.call_recorder(lambda obj: None)
    celery_task_method = pretend.call_recorder(lambda *a, **kw: task)
    celery_app = pretend.stub(task=celery_task_method)
    registry = pretend.stub(celery_app=celery_app)
    venusian_scanner = pretend.stub(config=pretend.stub(registry=registry))

    # Test the registered callback creates the Celery Task
    name = 'ignored'
    obj = check
    callback(venusian_scanner, name, obj)

    # Checks the decorator passed in our Celery task parameters
    assert celery_task_method.calls == [
        pretend.call(**task_kwargs),
    ]
    # Checks the function was created as a task
    assert task.calls == [pretend.call(check)]


def test_make_celery_app():
    celery_app = pretend.stub()
    config = pretend.stub(registry=pretend.stub(celery_app=celery_app))
    assert press_tasks._get_celery_app(config) is celery_app


def test_includeme(monkeypatch):
    broker_url = 'x-amqp://yyy'
    config = pretend.stub(
        action=pretend.call_recorder(lambda *a, **kw: None),
        add_directive=pretend.call_recorder(lambda *a, **kw: None),
        registry=pretend.stub(settings={'celery.broker': broker_url})
    )

    # monkeypatch the 'Celery.set_default' method so we know it was called.
    set_default = pretend.call_recorder(lambda *a, **kw: None)
    monkeypatch.setattr('celery.Celery.set_default', set_default)

    # Call the target includeme
    press_tasks.includeme(config)

    # Check for Celery object on the registry
    assert isinstance(config.registry.celery_app, Celery)
    assert config.registry.celery_app.main == 'press'
    assert config.registry.celery_app.autofinalize is False

    # Check the Celery object has been given a broker URL
    assert config.registry.celery_app.conf['broker_url'] == broker_url

    # Check for our override of the existing Task class
    assert config.registry.celery_app.Task is press_tasks.PyramidAwareTask

    # Check we set the default celery app
    assert config.registry.celery_app.set_default.calls

    # Check for action and directive registration
    assert config.action.calls == [
        pretend.call(
            ('celery', 'finalize'),
            config.registry.celery_app.finalize,
        ),
    ]
    assert config.add_directive.calls == [
        pretend.call(
            'make_celery_app',
            press_tasks._get_celery_app,
        ),
    ]
