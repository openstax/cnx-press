==========
Change Log
==========

2.0.0
-----

- Move the database connection creation into the publishing view code
  so that a single transaction can be pushed down through the functions.
- Refactor the testing persistence utility. And correct the versioning usage
  similar to what previous changes addressed except in the testing code.
- On publish assign ``major_version`` rather than ``version`` to prevent
  the database triggers that deal with legacy content from manipulating
  the record and invoking revision publications.
  See https://github.com/Connexions/cnx-press/issues/53
- Fix issue parsing abstracts that contain cnxml.
- Adjust ``make test`` to use an extended docker-compose configuration.
  Test runs should now use
  ``docker-compose -f docker-compose.yml -f docker-compose.test.yml ...``.
  This specifically enables the user to have a separate testing database
  from the one the one used by the app running via ``make serve``.
  See https://github.com/Connexions/cnx-press/pull/44
- Remove temporary ``FIXME`` workaround for the missing 'cnxorg' namespace
  by installing ``cnx-litezip==1.3.1``.
  See https://github.com/Connexions/cnx-press/pull/43
- Refactor legacy_publishing module into a package.
- Rename ``press.views.publishing`` module
  to ``press.views.legacy_publishing``.

1.0.0
-----

- Initial release
