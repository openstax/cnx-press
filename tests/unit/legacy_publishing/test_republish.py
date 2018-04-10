import pretend

from press.legacy_publishing.republish import (
    republish_books,
)


# To enable an ANY value when matching with pretend.call_recorder
# From https://github.com/alex/pretend/issues/7
class _Any:
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


ANY = _Any()


def test_republish_books(monkeypatch, content_util):
    shared_modules = [content_util.gen_module() for _ in range(0, 3)]
    collection = content_util.gen_collection(modules=list(shared_modules))[0]

    module_identifiers = [
        ('<uuid-1>', (3, None)),
        ('<uuid-2>', (4, None)),
        ('<uuid-3>', (5, None)),
    ]
    assert len(module_identifiers) == len(shared_modules)
    collections_containing_modules = {
        ('<uuid-11>', (1, 2)): ('<col-11>', '1.1'),
        ('<uuid-22>', (1, 13)): ('<col-22>', '1.1'),
    }
    results = [
        pretend.stub(
            __iter__=lambda: iter(module_identifiers)),
        pretend.stub(
            __iter__=lambda: iter(collections_containing_modules.keys())),
        pretend.stub(
            __iter__=lambda: iter(collections_containing_modules.values())),
    ]
    execute = pretend.call_recorder(lambda *a, **kw: results.pop(0))

    transaction = pretend.stub(
        __enter__=lambda: transaction,
        __exit__=lambda *a, **kw: None,
        execute=execute,
    )
    engine = pretend.stub(begin=lambda: transaction)
    registry = pretend.stub(engines={'common': engine})

    republished_collections = [('<uuid-11>', (1, 3)), ('<uuid-22>', (1, 14))]
    republish_collection = pretend.call_recorder(
        lambda t, i, v, cm: republished_collections.pop(0))
    monkeypatch.setattr(
        'press.legacy_publishing.republish.republish_collection',
        republish_collection,
    )

    republished_items = republish_books(
        collection,
        shared_modules,
        ('user1', 'test publish',),
        registry,
    )

    assert republished_items == list(collections_containing_modules.values())

    expected_calls = [
        pretend.call(ANY, moduleids=[m.id for m in shared_modules]),
        pretend.call(ANY, moduleids=[m.id for m in shared_modules],
                     collection_id=collection.id),
        pretend.call(ANY, identifiers=['<uuid-11>@1.3', '<uuid-22>@1.14']),
    ]
    assert execute.calls == expected_calls

    expected_calls = [
        pretend.call(ANY, '<uuid-11>', (1, 2), dict(module_identifiers)),
        pretend.call(ANY, '<uuid-22>', (1, 13), dict(module_identifiers)),
    ]
    assert republish_collection.calls == expected_calls
