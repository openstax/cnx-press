import pretend

from press.publishing.helpers import (
    bump_version,
    get_previous_published_version,
)


class TestBumpVersion:

    def test_module_major_version_bump(self):
        uuid = None
        major_version, minor_version = (4, None)
        row = ('Module', major_version, minor_version)
        db_result = pretend.stub(fetchone=lambda: row)
        db_transaction = pretend.stub(execute=lambda _: db_result)

        version = bump_version(db_transaction, uuid)

        expected_version = (major_version + 1, minor_version)
        assert version == expected_version

    def test_module_minor_version_bump(self):
        uuid = None
        major_version, minor_version = (4, None)
        row = ('Module', major_version, minor_version)
        db_result = pretend.stub(fetchone=lambda: row)
        db_transaction = pretend.stub(execute=lambda _: db_result)

        version = bump_version(db_transaction, uuid, is_minor_bump=True)

        expected_version = (major_version + 1, minor_version)
        assert version == expected_version

    def test_collection_major_version_bump(self):
        uuid = None
        major_version, minor_version = (4, 5)
        row = ('Collection', major_version, minor_version)
        db_result = pretend.stub(fetchone=lambda: row)
        db_transaction = pretend.stub(execute=lambda _: db_result)

        version = bump_version(db_transaction, uuid)

        expected_version = (major_version + 1, minor_version)
        assert version == expected_version

    def test_collection_minor_version_bump(self):
        uuid = None
        major_version, minor_version = (4, 5)
        row = ('Collection', major_version, minor_version)
        db_result = pretend.stub(fetchone=lambda: row)
        db_transaction = pretend.stub(execute=lambda _: db_result)

        version = bump_version(db_transaction, uuid, is_minor_bump=True)

        expected_version = (major_version, minor_version + 1)
        assert version == expected_version


class TestGetPreviousPublishedVersion:

    def test_for_module(self):
        uuid = '<uuid>'
        major_version, minor_version = (4, None)

        row = (major_version - 1, None)
        db_result = pretend.stub(fetchone=lambda: row)
        db_transaction = pretend.stub(execute=lambda _: db_result)

        version = get_previous_published_version(
            db_transaction, uuid, (major_version, minor_version))

        expected_version = (major_version - 1, minor_version)
        assert version == expected_version

    def test_without_previous_version(self):
        uuid = '<uuid>'
        major_version, minor_version = (1, 1)

        row = None
        db_result = pretend.stub(fetchone=lambda: row)
        db_transaction = pretend.stub(execute=lambda _: db_result)

        version = get_previous_published_version(
            db_transaction, uuid, (major_version, minor_version))

        expected_version = (None, None)
        assert version == expected_version
