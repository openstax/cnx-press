==========
Change Log
==========
8.1.9
-----

- Scheduled weekly dependency update for week 44 (#488)

8.1.8
-----

- Update sentry-sdk to 0.17.3 (#487)

8.1.7
-----

- Scheduled weekly dependency update for week 33 (#486)

8.1.6
-----

- Scheduled weekly dependency update for week 29

8.1.5
-----

- Scheduled weekly dependency update for week 26 (#483)

8.1.4
-----

- Pyup scheduled update 2020 06 04 (#482)

8.1.3
-----

- Upgrade cnxmlutils to 2.0.0 (#481)

8.1.2
-----

- Scheduled weekly dependency update for week 16 (#479)

8.1.1
-----

- Upgrade pinnings of various third-party dependencies
- Fix "fixture db_tables called directly" in tests (#463)

8.1.0
-----

- Upgrade pinnings of various third-party dependencies
- Fix Travis-CI build configuration (#449)
- Fix intermittent test failures when no rev-ing changes (#452)

8.0.2
-----

- Fix #347 Subjectlist should not be required for publish

8.0.1
-----

- Fix Sentry integration to not depend on the sentry-sdk package. This ensures
  the intergration is strictly optional.

8.0.0
-----

- Undo temporary policy to disallow changes to collection.xml files
- Create a collection xml parser
- Add the ability to detect when to major rev and when to minor rev

7.3.0
-----

- Update Sentry integration to use the Sentry SDK rather than the Raven client
  with custom integration code.

7.2.0
-----

- Prevent any changes to collection.xml files
- Only publish changed modules

7.1.1
-----

- Dry out ping API and add swagger docs



7.1.0
-----

- Preemptively check credentials when publishing via extending ping API

7.0.1
-----

- Move resource definitions into cnx-litezip
- correct content gen in tests

7.0.0
-----

- Allow publishing of images and other resources

6.0.1
-----

- Correct name of Maintainer role to match legacy

6.0.0
-----

- Added authentication for publishing

5.0.1
-----

- Added Cache-Control headers disallowing caching

5.0.0
-----

- Publish minor version of collection, rather than major

4.1.1
-----

- Fix publish submission logic to use the existing 'created' value
  rather than reading it from the xml document's metadata.
  See https://github.com/Connexions/cnx-press/issues/148

4.1.0
-----

- Add functionality to stop accidently overwriting others published changes

4.0.0
-----

- Add Celery to the project to move non-critical-path event handling logic
  to asynchronous tasks.
- Revise the subscriber communication to update the legacy 'latest' version.
  This procedure is now an asynchronous out-of-band task. The custom
  request retry behavior has been removed in favor of Celery's retry behavior.

3.4.2
-----

- Fix ``AttributeError: 'NoneType' object has no attribute 'abstractid'``.
  See https://github.com/Connexions/cnx-press/issues/132

3.4.1
-----

- Fix abstract publishing by finding and re-useing the existing abstract
  in the database rather than inserting a new matching abstract. Only if
  the abstract does not match do we insert a new abstract.
  See https://github.com/Connexions/cnx-press/issues/126

3.4.0
-----

- Fix and support the publication of derived works to maintain parentage
  information. This bit of information was being dropped during publication.
  See https://github.com/Connexions/cnx-press/issues/126

3.3.1
-----

- (dependency pinning updates)

3.3.0
-----

- Adds an publication finished event subscriber to request the 'latest'
  version of the content from the legacy software to have it read
  the latest version from the database, thus allowing it to have an
  updated object representation of the data for use with other requests.

3.2.4
-----

- Fix error log entry in the cache purging subscriber
  to only output the content ids within the context of the loop cycle.

3.2.3
-----

- One more attempt to address legacy enqueuing read timeouts (caused
  by DB conflicts in zope) by retrying failed enqueuing attempts.

3.2.2
-----

- Address legacy enqueuing read timeouts by sorting the content so that
  the collection is sent first. All other requests can timeout
  without concern. This only addresses the problem and does not fully
  resolve it.
  See https://github.com/Connexions/cnx-press/issues/100

3.2.1
-----

- Fix internal usage of the version by consistently using a version
  tuple (major and minor) between functions rather than the legacy version.

3.2.0
-----

- Add a publication finished event subscriber that purges the cache
  for legacy urls that contain the 'latest' version classifier.

3.1.0
-----

- Add events to legacy publications. This enables other subscriber code
  to hook into these events.

- Add the raven client as a request method. This allows non-critical error
  handling to report issues without bubbling it up through the main process.

- Add publication finished event subscriber that contacts the legacy
  service to enqueue the content for export file builds (i.e. completezip,
  collxml, module export).
  See https://github.com/Connexions/nebuchadnezzar/issues/44

- Add a publication finished event subscriber that tracks publications to
  the filesystem. This is used primiarly as a safe guard incase we decide
  or need to enable the "republishing" of books with shared pages.

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
