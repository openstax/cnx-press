from dateutil.parser import parse as parse_date
from sqlalchemy.sql import text

from press.legacy_publishing import (
    publish_legacy_book,
    publish_legacy_page,
    publish_litezip,
)
from press.parsers import (
    parse_collection_metadata,
    parse_module_metadata,
)


def test_publish_revision_to_legacy_page(
        content_util, persist_util, app, db_engines, db_tables):
    module = content_util.gen_module()
    module = persist_util.insert_module(module)

    metadata = parse_module_metadata(module)

    registry = app.registry
    ident = publish_legacy_page(module, metadata,
                                ('user1', 'test publish',),
                                registry)

    # Check core metadata insertion
    stmt = (db_tables.modules.join(db_tables.abstracts)
            .select()
            .where(db_tables.modules.c.module_ident == ident))
    result = db_engines['common'].execute(stmt).fetchone()
    assert result.version == '1.2'
    assert result.abstract == metadata.abstract
    assert result.created == parse_date(metadata.created)
    assert result.revised == parse_date(metadata.revised)
    assert result.portal_type == 'Module'
    assert result.name == metadata.title
    assert result.licenseid == 13
    assert result.submitter == 'user1'
    assert result.submitlog == 'test publish'
    assert result.authors == list(metadata.authors)
    assert result.maintainers == list(metadata.maintainers)
    assert result.licensors == list(metadata.licensors)

    # Check subject metadata insertion
    stmt = (db_tables.moduletags.join(db_tables.tags)
            .select()
            .where(db_tables.moduletags.c.module_ident == ident))
    results = db_engines['common'].execute(stmt)
    subjects = [x.tag for x in results]
    assert sorted(subjects) == sorted(metadata.subjects)

    # Check keyword metadata insertion
    stmt = (db_tables.modulekeywords.join(db_tables.keywords)
            .select()
            .where(db_tables.modulekeywords.c.module_ident == ident))
    results = db_engines['common'].execute(stmt)
    keywords = [x.word for x in results]
    assert sorted(keywords) == sorted(metadata.keywords)

    # Check for file insertion
    stmt = (db_tables.module_files
            .join(db_tables.files)
            .select()
            .where(db_tables.module_files.c.module_ident == ident))
    result = db_engines['common'].execute(stmt).fetchall()
    filenames = [x.filename for x in result]
    assert 'index.cnxml' in filenames
    assert 'index.cnxml.html' in filenames

    # TODO Check for resource file insertion


def compare_tree_similarity(db_tree, test_tree):
    """Compare the two types of tree, one coming from the database using
    `tree_to_json_for_legacy` and the other using the tree structure
    provided by the `content_util` testing utility.

    """
    for i, v in enumerate(db_tree):
        if v['id'].startswith('col'):
            assert test_tree[i].title == v['title']
            compare_tree_similarity(v['contents'], test_tree[i].contents)
        else:
            node = test_tree[i]
            assert v['id'] == node.id
            assert v['title'] == node.title
            assert v['version'] == node.version_at


def test_publish_legacy_book(
        content_util, persist_util, app, db_engines, db_tables):
    # Insert initial collection and modules.
    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)
    metadata = parse_collection_metadata(collection)

    # Insert a new module ...
    new_module = content_util.gen_module()
    new_module = persist_util.insert_module(new_module)
    # ... remove second element from the tree ...
    tree.pop(1)
    # ... and append the new module to the tree.
    tree.append(content_util.make_tree_node_from(new_module))
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)

    registry = app.registry
    ident = publish_legacy_book(collection, metadata,
                                ('user1', 'test publish',),
                                registry)

    # Check core metadata insertion
    stmt = (db_tables.modules.join(db_tables.abstracts)
            .select()
            .where(db_tables.modules.c.module_ident == ident))
    result = db_engines['common'].execute(stmt).fetchone()
    assert result.version == '1.2'
    assert result.abstract == metadata.abstract
    assert result.created == parse_date(metadata.created)
    assert result.revised == parse_date(metadata.revised)
    assert result.portal_type == 'Collection'
    assert result.name == metadata.title
    assert result.licenseid == 13
    assert result.submitter == 'user1'
    assert result.submitlog == 'test publish'
    assert result.authors == list(metadata.authors)
    assert result.maintainers == list(metadata.maintainers)
    assert result.licensors == list(metadata.licensors)

    # Check subject metadata insertion
    stmt = (db_tables.moduletags.join(db_tables.tags)
            .select()
            .where(db_tables.moduletags.c.module_ident == ident))
    results = db_engines['common'].execute(stmt)
    subjects = [x.tag for x in results]
    assert sorted(subjects) == sorted(metadata.subjects)

    # Check keyword metadata insertion
    stmt = (db_tables.modulekeywords.join(db_tables.keywords)
            .select()
            .where(db_tables.modulekeywords.c.module_ident == ident))
    results = db_engines['common'].execute(stmt)
    keywords = [x.word for x in results]
    assert sorted(keywords) == sorted(metadata.keywords)

    # Check for file insertion
    stmt = (db_tables.module_files
            .join(db_tables.files)
            .select()
            .where(db_tables.module_files.c.module_ident == ident))
    result = db_engines['common'].execute(stmt).fetchall()
    filenames = [x.filename for x in result]
    assert 'collection.xml' in filenames

    # TODO Check for resource file insertion

    # Check the tree for accuracy (even though this is out of scope)
    stmt = (
        text("SELECT tree_to_json_for_legacy("
             "  m.uuid::text, "
             "  concat_ws('.', m.major_version, m.minor_version)::text"
             ")::json "
             "FROM modules AS m "
             "WHERE m.module_ident = :module_ident")
        .bindparams(module_ident=ident))
    inserted_tree = db_engines['common'].execute(stmt).fetchone()[0]
    compare_tree_similarity(inserted_tree['contents'], tree)


def test_publish_litezip(db_engines, db_tables):
    publish_litezip
    pass
