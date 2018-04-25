==========
Change Log
==========

?.?.?
-----

- Add events to legacy publications. This enables other subscriber code
  to hook into these events.

3.0.0
-----

- Fix to insert the missing print-style into the metadata record.
  See https://github.com/Connexions/cnx-press/issues/86

- Fix broken links in content by making the resource available during
  reference resolution. By inserting the resources after the content,
  we were asking the reference resolution code to look for resources that
  did not exist yet. The fix simply puts the resource insertion about the
  content insertion.
  See https://github.com/Connexions/nebuchadnezzar/issues/40

- Carry over the Google Analytics code from the previous publication.
  We don't yet have a way to set this in the content
  or during the publication. Later work will likely address this.
  See https://github.com/Connexions/cnx-press/issues/84

- Let the database set the revised content timestamp, which is associated
  with when the last publish was made.
  See https://github.com/Connexions/cnx-press/issues/81 &
  https://github.com/Connexions/nebuchadnezzar/issues/35

- Change ``/api/v3/publish`` to ``/api/publish-litezip``, because
  the OpenStax developer community is favoring api versioning by HTTP header.

2.0.1
-----

- Fix issue with published content missing resources. This was because we
  don't link the previous versions resources to the newly published version.
  See https://github.com/Connexions/nebuchadnezzar/issues/23
- Fix publication insertion to use the existing UUID for content rather
  than create a new UUID.
  See https://github.com/Connexions/cnx-press/issues/75

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
