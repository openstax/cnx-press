from dateutil.parser import parse as parse_date
from litezip.main import COLLECTION_NSMAP
from sqlalchemy.sql import text

from press.legacy_publishing.collection import (
    publish_legacy_book,
)
from press.parsers import (
    parse_collection_metadata,
)

from tests.conftest import GOOGLE_ANALYTICS_CODE
from tests.helpers import (
    compare_legacy_tree_similarity,
    element_tree_from_model,
)


def test_publish_revision(
        content_util, persist_util, app, db_engines, db_tables):
    # Insert initial collection and modules.
    resources = list([content_util.gen_resource() for x in range(0, 2)])
    collection, tree, modules = content_util.gen_collection(
        resources=resources
    )
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)
    metadata = parse_collection_metadata(collection)

    # Collect control data for non-legacy metadata
    stmt = (
        db_tables.modules.select()
        .where(db_tables.modules.c.moduleid == metadata.id)
    )
    control_metadata = db_engines['common'].execute(stmt).fetchone()

    # Insert a new module ...
    new_module = content_util.gen_module()
    new_module = persist_util.insert_module(new_module)
    # ... remove second element from the tree ...
    tree.pop(1)
    # ... and append the new module to the tree.
    tree.append(content_util.make_tree_node_from(new_module))
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)

    # TARGET
    with db_engines['common'].begin() as conn:
        now = conn.execute('SELECT CURRENT_TIMESTAMP as now').fetchone().now
        (id, version), ident = publish_legacy_book(
            collection,
            metadata,
            ('user1', 'test publish',),
            conn,
        )

    # Check core metadata insertion
    stmt = (
        db_tables.modules
        .select()
        .where(db_tables.modules.c.module_ident == ident)
    )
    result = db_engines['common'].execute(stmt).fetchone()
    assert result.uuid == control_metadata.uuid
    assert result.major_version == 2
    assert result.minor_version == 1
    assert result.version == '1.2'
    assert result.abstractid == control_metadata.abstractid
    assert result.created == parse_date(metadata.created)
    assert result.revised == now
    assert result.portal_type == 'Collection'
    assert result.name == metadata.title
    assert result.licenseid == 13
    assert result.print_style == metadata.print_style
    assert result.submitter == 'user1'
    assert result.submitlog == 'test publish'
    assert result.authors == list(metadata.authors)
    assert result.maintainers == list(metadata.maintainers)
    assert result.licensors == list(metadata.licensors)
    assert result.google_analytics == GOOGLE_ANALYTICS_CODE

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
    assert len(filenames) == len(resources) + 1  # content file
    assert 'collection.xml' in filenames

    # Check for resource file insertion
    for resource in resources:
        assert resource.filename in filenames

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
    compare_legacy_tree_similarity(inserted_tree['contents'], tree)


def test_publish_revision_with_new_abstract(
        content_util, persist_util, app, db_engines, db_tables):
    # Insert initial collection and modules.
    resources = list([content_util.gen_resource() for x in range(0, 2)])
    collection, tree, modules = content_util.gen_collection(
        resources=resources
    )
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)
    with element_tree_from_model(collection) as xml:
        elm = xml.xpath('//md:abstract', namespaces=COLLECTION_NSMAP)[0]
        elm.text += ' -- appendage'
    metadata = parse_collection_metadata(collection)

    # Collect control data for non-legacy metadata
    stmt = (
        db_tables.modules.select()
        .where(db_tables.modules.c.moduleid == metadata.id)
    )
    control_metadata = db_engines['common'].execute(stmt).fetchone()

    # Insert a new module ...
    new_module = content_util.gen_module()
    new_module = persist_util.insert_module(new_module)
    # ... remove second element from the tree ...
    tree.pop(1)
    # ... and append the new module to the tree.
    tree.append(content_util.make_tree_node_from(new_module))
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)

    # TARGET
    with db_engines['common'].begin() as conn:
        (id, version), ident = publish_legacy_book(
            collection,
            metadata,
            ('user1', 'test publish',),
            conn,
        )

    # Check core metadata insertion
    stmt = (
        db_tables.modules
        .select()
        .where(db_tables.modules.c.module_ident == ident)
    )
    result = db_engines['common'].execute(stmt).fetchone()
    assert result.abstractid != control_metadata.abstractid


def test_publish_derived(
        content_util, persist_util, app, db_engines, db_tables):
    # Insert initial collection and modules.
    resources = list([content_util.gen_resource() for x in range(0, 2)])
    collection, tree, modules = content_util.gen_collection(
        resources=resources
    )
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)
    metadata = parse_collection_metadata(collection)

    # Derive a copy of the collection
    derived_collection = persist_util.derive_from(collection)
    derived_metadata = parse_collection_metadata(derived_collection)

    # Collect control data for non-legacy metadata
    stmt = (
        db_tables.modules.select()
        .where(db_tables.modules.c.moduleid == derived_metadata.id)
    )
    control_metadata = db_engines['common'].execute(stmt).fetchone()

    # TARGET
    with db_engines['common'].begin() as conn:
        now = conn.execute('SELECT CURRENT_TIMESTAMP as now').fetchone().now
        (id, version), ident = publish_legacy_book(
            derived_collection,
            derived_metadata,
            ('user1', 'test publish',),
            conn,
        )

    # Lookup parent collection's metadata (ident and authors)
    # for parentage checks against the derived-copy metadata.
    stmt = (
        db_tables.latest_modules
        .select()
        .where(db_tables.latest_modules.c.moduleid == collection.id)
    )
    parent_metadata_result = db_engines['common'].execute(stmt).fetchone()

    # Check core metadata insertion
    stmt = (
        db_tables.modules.join(db_tables.abstracts)
        .select()
        .where(db_tables.modules.c.module_ident == ident)
    )
    result = db_engines['common'].execute(stmt).fetchone()
    assert result.uuid == control_metadata.uuid
    assert result.major_version == 2
    assert result.minor_version == 1
    assert result.version == '1.2'
    assert result.abstract == derived_metadata.abstract
    assert result.created == parse_date(derived_metadata.created)
    assert result.revised == now
    assert result.portal_type == 'Collection'
    assert result.name == derived_metadata.title
    assert result.licenseid == 13
    assert result.print_style == derived_metadata.print_style
    assert result.submitter == 'user1'
    assert result.submitlog == 'test publish'
    assert result.authors == list(derived_metadata.authors)
    assert result.maintainers == list(derived_metadata.maintainers)
    assert result.licensors == list(derived_metadata.licensors)
    assert result.google_analytics == GOOGLE_ANALYTICS_CODE

    # Check for derived metadata (parent and parent authors)
    assert result.parent == parent_metadata_result.module_ident
    assert result.parentauthors == parent_metadata_result.authors

    # Check the derived-from metadata tag was correctly inserted
    # into the document.
    stmt = (
        db_tables.module_files
        .join(db_tables.files)
        .select()
        .where(db_tables.module_files.c.module_ident == ident)
        .where(db_tables.module_files.c.filename == 'collection.xml')
    )
    collection_doc = db_engines['common'].execute(stmt).fetchone()
    expected = bytes(
        ('<md:derived-from url="http://cnx.org/content/{}/{}"/>'
         .format(metadata.id, metadata.version)),
        'utf-8',
    )
    assert expected in collection_doc.file
