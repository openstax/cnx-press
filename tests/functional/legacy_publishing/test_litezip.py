from sqlalchemy.sql import text
from press.legacy_publishing.litezip import (
    publish_litezip,
)
from tests.helpers import (
    compare_legacy_tree_similarity,
)


def test_publish_litezip(
        content_util, persist_util, app, db_engines, db_tables):
    # Insert initial collection and modules.
    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)

    # Insert a new module ...
    new_module = content_util.gen_module(relative_to=collection)
    new_module = persist_util.insert_module(new_module)
    # ... remove second element from the tree ...
    tree.pop(1)
    # ... and append the new module to the tree.
    tree.append(content_util.make_tree_node_from(new_module))

    # Change the module text, to make it publishable.
    index_cnxml = new_module.file.read_text()
    start_offset = index_cnxml.find('test document')
    new_module.file.write_text(index_cnxml[:start_offset] +
                               'TEST DOCUMENT' +
                               index_cnxml[start_offset + 13:])

    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    struct = tuple([collection, new_module])

    with db_engines['common'].begin() as conn:
        id_map = publish_litezip(
            struct,
            ('user1', 'test publish',),
            conn,
        )

    expected_id_map = {
        new_module.id: (new_module.id, (2, None)),
        collection.id: (collection.id, (2, 1)),
    }
    assert expected_id_map == id_map

    # Update the tree to reflect the Module publication above.
    tree[-1].version_at = '1.2'

    # Check the collection tree for accuracy. (This is not out of scope,
    # because the collection.xml document needs modified before insertion.)
    stmt = (
        text("SELECT tree_to_json_for_legacy("
             "  m.uuid::text, "
             "  concat_ws('.', m.major_version, m.minor_version)::text"
             ")::json "
             "FROM modules AS m "
             "WHERE m.moduleid = :moduleid "
             "AND m.major_version = :major_version "
             "AND m.minor_version = :minor_version")
        .bindparams(moduleid=collection.id, major_version=2, minor_version=1))
    inserted_tree = db_engines['common'].execute(stmt).fetchone()[0]
    compare_legacy_tree_similarity(inserted_tree['contents'], tree)


def test_publish_litezip_collectionxml_only(
        content_util, persist_util, app, db_engines, db_tables):
    # Insert initial collection and modules.
    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)

    # ... remove second element from the tree ...
    tree.pop(1)

    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    struct = tuple([collection])

    with db_engines['common'].begin() as conn:
        id_map = publish_litezip(
            struct,
            ('user1', 'test publish collection.xml',),
            conn,
        )

    expected_id_map = {
        collection.id: (collection.id, (2, 1)),
    }
    assert expected_id_map == id_map

    # Check the collection tree for accuracy. (This is not out of scope,
    # because the collection.xml document needs modified before insertion.)
    stmt = (
        text("SELECT tree_to_json_for_legacy("
             "  m.uuid::text, "
             "  concat_ws('.', m.major_version, m.minor_version)::text"
             ")::json "
             "FROM modules AS m "
             "WHERE m.moduleid = :moduleid "
             "AND m.major_version = :major_version "
             "AND m.minor_version = :minor_version")
        .bindparams(moduleid=collection.id, major_version=2, minor_version=1))
    inserted_tree = db_engines['common'].execute(stmt).fetchone()[0]
    compare_legacy_tree_similarity(inserted_tree['contents'], tree)


def test_publish_litezip_minor_rev(
        content_util, persist_util, app, db_engines, db_tables):
    # Insert initial collection and modules.
    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)

    # Modify the module text.
    index_cnxml = modules[0].file.read_text()
    start_offset = index_cnxml.find('test document')
    modules[0].file.write_text(index_cnxml[:start_offset] +
                               'TEST DOCUMENT' +
                               index_cnxml[start_offset + 13:])

    struct = tuple([collection, modules[0]])

    with db_engines['common'].begin() as conn:
        id_map = publish_litezip(
            struct,
            ('user1', 'test publish module',),
            conn,
        )

    expected_id_map = {
        modules[0].id: (modules[0].id, (2, None)),
        collection.id: (collection.id, (1, 2)),
    }
    assert expected_id_map == id_map

    # Update the tree to reflect the Module publication above.
    for node in content_util.flatten_collection_tree_to_nodes(tree):
        if getattr(node, 'id', None) == modules[0].id:
            node.version_at = '1.2'

    # Check the collection tree for accuracy. (This is not out of scope,
    # because the collection.xml document needs modified before insertion.)
    stmt = (
        text("SELECT tree_to_json_for_legacy("
             "  m.uuid::text, "
             "  concat_ws('.', m.major_version, m.minor_version)::text"
             ")::json "
             "FROM modules AS m "
             "WHERE m.moduleid = :moduleid "
             "AND m.major_version = :major_version "
             "AND m.minor_version = :minor_version")
        .bindparams(moduleid=collection.id, major_version=1, minor_version=2))
    inserted_tree = db_engines['common'].execute(stmt).fetchone()[0]
    compare_legacy_tree_similarity(inserted_tree['contents'], tree)
