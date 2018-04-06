import pretend

from press.publishing.republish import republish_collection


class TestRepublishCollection:

    def test(self, monkeypatch):
        uuid = '<uuid>'
        major_version, minor_version = (4, 5)
        next_mjr_version, next_mnr_version = major_version, minor_version + 1
        bump_version = pretend.call_recorder(
            lambda t, i, is_minor_bump: (major_version, minor_version + 1))

        monkeypatch.setattr(
            'press.publishing.republish.bump_version',
            bump_version
        )

        row = (uuid, next_mjr_version, next_mnr_version)
        db_result = pretend.stub(fetchone=lambda: row)
        db_transaction = pretend.stub(execute=lambda _: db_result)

        id, version = republish_collection(
            db_transaction, uuid, (major_version, minor_version))

        assert id == uuid
        assert version == (next_mjr_version, next_mnr_version)

        expected_call = pretend.call(db_transaction, uuid, is_minor_bump=True)
        assert bump_version.calls == [expected_call]
