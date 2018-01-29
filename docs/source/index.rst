CNX Press
=========

.. _Nebuchadnezzar: https://github.com/Connexions/nebuchadnezzar


The Press service is a short lived project
to give Content Managers the ability
to circumvent interaction with the CNX Zope based product.
The product deployed as a production service will run in
the CNX Cloud space as a HTTP API for use by Content Managers.

This product falls under the Content Production Tools (CPT) product set.
The main interaction with this product is via the `Nebuchadnezzar`_
(a.k.a. ``nebu``).

The CNX Press product has two components:

* Command-line interface (CLI) -- Used by Content Managers
  to acquire and submit content for validation, preview and publication.
* HTTP API -- Interacted with via the CLI to provide content validation,
  preview and publication.

The HTTP API is a separate service from existing services
(archive, publishing and authoring),
because it will change architectural roles throughout its lifetime
(from a publishing component to an authoring component).

Nebuchadnezzar_ requires only minimal dependencies,
because the brunt of the work will be done in this product.
It's anticipated the Nebuchadnezzar usage and workflow
a Content Manager uses will largely remain the same over time.
However the HTTP API will change to adapt to changes and the feature timeline.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   config.rst
   web_api.rst
   api.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
