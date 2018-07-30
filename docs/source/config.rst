.. _configuration_chapter:

=============
Configuration
=============

.. _configuration_chapter__settings:

Settings
--------

The application is configured via environment variables.
The following application settings are mapped to environment variables.

===============================  ======================  =============
Setting                          Env Variable            Required?
===============================  ======================  =============
``db.common.url``                ``DB_URL``              yes
``db.readonly.url``              ``DB_READONLY_URL``     no
``db.super.url``                 ``DB_SUPER_URL``        no
``shared_directory``             ``SHARED_DIR``          yes
``debug``                        ``DEBUG``               no
``logging.level``                ``DEBUG``               no
``sentry.dsn``                   ``SENTRY_DSN``          no
``celery.broker``                ``AMQP_URL``            yes
===============================  ======================  =============

See `cnx-db configuration docs
<https://cnx-db.readthedocs.io/en/latest/config.html>`_
for more information about configuring the database features.

For information on how the configuration is coded see,
:func:`press.config.configure`.

.. _configuration_chapter__logging:

Logging
-------

The logging configuration is by default set to ``INFO`` level logging.
If you wish to receive ``DEBUG`` level logging you should set the
``DEBUG`` environment variable to ``true``.

.. _configuration_chapter__asynchronous_tasks:

Celery Asynchronous Tasks
-------------------------

We use `Celery <http://www.celeryproject.org/>`_
with an AMQP enabled queue (i.e. `RabbitMQ <https://www.rabbitmq.com/>`_)
to provide components of our application
to run as asynchronous tasks
outside the scope of a request and response cycle.
This is configured via ``AMQP_URL``
(e.g. ``amqp://guest@rabbitmq:5672//``).

For information about how to use implement tasks,
see :ref:`asynchronous_tasks_chapter`
and the :func:`press.tasks.task` decorator.

.. _configuration_chapter__error_reporting:

Error Reporting
---------------

This application contains integration code to report errors
to a `Sentry <https://sentry.io>`_ instance.
The integration can be configured by supplying the ``SENTRY_DSN``,
which is usually provided to you during your projects setup
in the sentry software.
