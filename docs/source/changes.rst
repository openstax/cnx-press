==========
Change Log
==========

?.?.?
-----

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

1.0.0
-----

- Initial release
