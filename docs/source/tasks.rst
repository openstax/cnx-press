.. _asynchronous_tasks_chapter:

==================
Asynchronous Tasks
==================

.. seealso::

   See also :ref:`configuration_chapter__asynchronous_tasks` for information
   on how to configure the queuing service.

.. _asynchronous_tasks_chapter__usage:

Usage
-----

To register a Celery Task, decorate a function with :func:`press.tasks.task`.
To use the Celery Task, call the ``task`` method on the request object.
For example::

  from pyramid.views import view_config
  from press.tasks import task

  @task(bind=True)
  def msg_slack(self, msg):
      request = self.get_pyramid_request()
      request.registry.slack_client.send('#cnx-stream', 'msg')

  @view_config(name='ping')
  def ping(request):
      request.task(msg_slack).delay('somebody pinged the site!')
      return 'pong'

.. note::

   The ``request.task(<task_func>).delay(...)`` usage might seem odd.
   Unlike the Celery provided task decorator, ours does not modify
   the function to make it a task. Thus, calling the function will
   not call any of the wrapping task logic. It remains the original
   function as defined.

   We do it this way because the Celery application isn't created
   until runtime.

.. note::

   You should be able to use the :func:`press.tasks.task` decorator
   the same way as
   `Celery's task decorator <http://docs.celeryproject.org/en/latest/reference/celery.html#celery.Celery.task>`_.

.. warning::

   The the execution usage
   (``request.task(<task_func>).delay(...)``)
   is not yet implemented.
