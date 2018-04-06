import pretend

from press.publishing.republish import (
    _rebuild_collection_tree,
    republish_collection
)


# To enable an ANY value when matching with pretend.call_recorder
# From https://github.com/alex/pretend/issues/7
class _Any:
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


ANY = _Any()


class TestRepublishCollection:

    def test(self, monkeypatch):
        uuid = '<uuid>'
        major_version, minor_version = (4, 5)
        next_mjr_version, next_mnr_version = major_version, minor_version + 1
        change_map = {}

        bump_version = pretend.call_recorder(
            lambda t, i, is_minor_bump: (major_version, minor_version + 1))
        monkeypatch.setattr(
            'press.publishing.republish.bump_version',
            bump_version
        )
        _rebuild_collection_tree = pretend.call_recorder(
            lambda trans, uuid, version, change_map: None)
        monkeypatch.setattr(
            'press.publishing.republish._rebuild_collection_tree',
            _rebuild_collection_tree
        )

        row = (uuid, next_mjr_version, next_mnr_version)
        db_result = pretend.stub(fetchone=lambda: row)
        db_transaction = pretend.stub(execute=lambda _: db_result)

        id, version = republish_collection(
            db_transaction,
            uuid,
            (major_version, minor_version),
            change_map,
        )

        assert id == uuid
        assert version == (next_mjr_version, next_mnr_version)

        assert change_map == {uuid: (next_mjr_version, next_mnr_version)}

        expected_call = pretend.call(db_transaction, uuid, is_minor_bump=True)
        assert bump_version.calls == [expected_call]


class TestRebuildCollectionTree:

    def test(self):
        uuid = '<uuid>'
        major_version, minor_version = (4, 5)
        next_mjr_version, next_mnr_version = major_version, minor_version + 1
        change_map = {
            uuid: (next_mjr_version, next_mnr_version),
            '<uuid-22>': (2, None),
            '<uuid-44>': (2, None),
        }

        tree_row_keys = [
            'nodeid', 'parent_id', 'documentid', 'title',
            'childorder', 'latest',
            'uuid', 'major_version', 'minor_version', 'path',
        ]
        tree_rows = [
            (1, None, 11, None, 0, None,
             uuid, major_version, minor_version, [1]),
            (2, 1, 22, 'twenty-two', 1, True,  # update to latest
             '<uuid-22>', 1, None, [1, 2]),
            (3, 1, 33, 'subcol', 2, None,
             '<uuid-33>', 2, 1, [1, 3]),
            (4, 3, 44, None, 3, False,  # do not update to latest
             '<uuid-44>', 1, None, [1, 3, 4]),
            (5, 3, 55, 'fifty-five', 4, None,
             '<uuid-55>', 1, None, [1, 3, 5])
        ]
        tree_rows = list([(dict(zip(tree_row_keys, x)),) for x in tree_rows])

        db_results = [
            # call for the tree data, which is iterated over
            pretend.stub(__iter__=lambda: iter(tree_rows)),
            # individual calls for a tree node insertion, returning nodeid
            pretend.stub(fetchone=lambda: (6,)),
            pretend.stub(fetchone=lambda: (7,)),
            pretend.stub(fetchone=lambda: (8,)),
            pretend.stub(fetchone=lambda: (9,)),
            pretend.stub(fetchone=lambda: (10,)),
        ]
        execute = pretend.call_recorder(lambda *a, **kw: db_results.pop(0))
        db_transaction = pretend.stub(execute=execute)

        _rebuild_collection_tree(
            db_transaction,
            uuid,
            (major_version, minor_version),
            change_map,
        )

        # Check the insert was called with the correct parameters
        # Note, the nodeid and path are ignored by the insert statement.
        expected_insert_calls = [
            # Note the change in the minor version
            pretend.call(ANY, nodeid=ANY, parent_id=None, documentid=11,
                         title=None, childorder=0, latest=None,
                         uuid='<uuid>', major_version=4, minor_version=6,
                         path=ANY),
            # Note the change in the parent and version
            pretend.call(ANY, nodeid=ANY, parent_id=6, documentid=22,
                         title='twenty-two', childorder=1, latest=True,
                         uuid='<uuid-22>', major_version=2,
                         minor_version=None, path=ANY),
            # Note the change in the parent
            pretend.call(ANY, nodeid=ANY, parent_id=6, documentid=33,
                         title='subcol', childorder=2, latest=None,
                         uuid='<uuid-33>', major_version=2, minor_version=1,
                         path=ANY),
            # Note the change in the parent and specifically not the version
            pretend.call(ANY, nodeid=ANY, parent_id=8, documentid=44,
                         title=None, childorder=3, latest=False,
                         uuid='<uuid-44>', major_version=1,
                         minor_version=None, path=ANY),
            # Note the change in the parent
            pretend.call(ANY, nodeid=ANY, parent_id=8, documentid=55,
                         title='fifty-five', childorder=4, latest=None,
                         uuid='<uuid-55>', major_version=1,
                         minor_version=None, path=ANY)]
        # Ignore the first execute call which retrieves the tree
        assert execute.calls[1:] == expected_insert_calls
