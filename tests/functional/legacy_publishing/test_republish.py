from sqlalchemy.sql import text

from press.legacy_publishing.republish import (
    republish_books,
)


def test_republish_books_including(
        content_util, persist_util, app, db_engines, db_tables):
    # Create four collections,
    #   A. collection sharing one module
    #   B. collection sharing one module differing from A
    #   C. collection sharing two modules
    # Test for one republication of collections A, B and C.

    shared_modules = [content_util.gen_module() for _ in range(0, 3)]
    shared_modules = list([persist_util.insert_module(m)
                           for m in shared_modules])

    # Insert collection A
    collection_a, _, __ = persist_util.insert_all(
        *content_util.gen_collection(modules=shared_modules[:1]))
    # Insert collection B
    collection_b, _, __ = persist_util.insert_all(
        *content_util.gen_collection(modules=shared_modules[1:2]))
    # Insert collection C
    collection_c, _, __ = persist_util.insert_all(
        *content_util.gen_collection(modules=shared_modules[1:]))

    # Adjust the shared modules and republish them
    shared_modules = [
        content_util.bump_version(content_util.append_to_module(m))
        for m in shared_modules
    ]
    shared_modules = list([persist_util.insert_module(m)
                           for m in shared_modules])
    contextual_collection = persist_util.insert_collection(
        content_util.gen_collection(modules=shared_modules)[0])
    # This acts as if a collection containing these modules has taken place.
    # We do not test the triggers have not fired, because that is outside
    # the scope of this test case. That test would be part of cnx-db.

    registry = app.registry
    republished_items = republish_books(
        contextual_collection,
        shared_modules,
        ('user1', 'test publish',),
        registry,
    )

    assert len(republished_items) == 3
    assert (collection_a.id, '1.1') in republished_items
    assert (collection_b.id, '1.1') in republished_items
    assert (collection_c.id, '1.1') in republished_items

    # Check for a republication, by simply checking the next version exists
    collection_ids = [collection_a.id, collection_b.id, collection_c.id]
    stmt = (
        text(
            'SELECT moduleid, '
            '  array_agg(concat_ws(\'-\', '
            '                      major_version, '
            '                      minor_version) '
            '            ORDER BY minor_version) '
            'FROM modules '
            'WHERE moduleid = any(:ids) '
            'GROUP BY moduleid')
        .bindparams(ids=collection_ids))
    result = db_engines['common'].execute(stmt)
    collections = dict(result.fetchall())
    expected_collections = dict(zip(collection_ids, [['1-1', '1-2']] * 3))
    assert collections == expected_collections

    # Check the collection tree contains the newly published module(s).
    stmt = (
        text(
            'SELECT tree_to_json_for_legacy('
            '  m.uuid::text, '
            '  module_version( m.major_version, m.minor_version)::text'
            ')::json '
            'FROM modules AS m '
            'WHERE m.moduleid = :moduleid AND m.minor_version = 2')
        .bindparams(moduleid=collection_a.id))
    inserted_tree = db_engines['common'].execute(stmt).fetchone()[0]
    collection_items = [
        (n['id'], n['version'],)
        for n in content_util.flatten_collection_tree_to_nodes(inserted_tree)
    ]
    assert (shared_modules[0].id, '1.2') in collection_items
