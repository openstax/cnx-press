import io

from datetime import timedelta
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
from tests.random_image import (
    generate_random_image_by_size,
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
    assert result.major_version == 1
    assert result.minor_version == 2
    assert result.version == '1.1'
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


# https://github.com/Connexions/cnx-press/issues/148
def test_publish_revision_with_created_value_changed(
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
        elm = xml.xpath('//md:created', namespaces=COLLECTION_NSMAP)[0]
        actual_created = parse_date(elm.text)
        changed_created = actual_created - (timedelta(days=365) * 8)
        elm.text = changed_created.isoformat()

    metadata = parse_collection_metadata(collection)

    # Collect control data for non-legacy metadata
    stmt = (
        db_tables.modules.select()
        .where(db_tables.modules.c.moduleid == metadata.id)
    )
    control_metadata = db_engines['common'].execute(stmt).fetchone()
    assert control_metadata.created == actual_created

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
    assert result.created == control_metadata.created
    assert result.created != changed_created


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

    # Make some change to the collection xml,
    # because republishing an unchanged collection is no longer valid
    with derived_collection.file.open('r+') as fb:
        new_content = fb.read().replace('Derived copy of', 'Deerived copy of')
        fb.seek(0)
        fb.write(new_content)

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
    assert result.major_version == 1
    assert result.minor_version == 2
    assert result.version == '1.1'
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


def test_publish_revision_with_new_resources(
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

    filename = 'book-cover.png'
    book_cover_img = generate_random_image_by_size(10)
    book_cover_data = io.BytesIO()
    book_cover_img.save(book_cover_data, 'PNG')
    book_cover_data.seek(0)
    book_cover = content_util.gen_resource(
        data=book_cover_data,
        filename=filename,
        media_type='image/png',
    )
    collection.resources.append(book_cover)

    # Collect control data for this current version
    stmt = (
        db_tables.module_files
        .join(db_tables.files)
        .select()
        .where(db_tables.modules.c.moduleid == metadata.id)
    )
    control_data = db_engines['common'].execute(stmt).fetchall()

    # Ensure the resource is not in the content
    # prior to our publication
    control_files = {x.filename: x for x in control_data}
    assert book_cover.filename not in control_files

    # TARGET
    with db_engines['common'].begin() as conn:
        (id, version), ident = publish_legacy_book(
            collection,
            metadata,
            ('user1', 'test publish',),
            conn,
        )

    # Check for file insertion
    stmt = (db_tables.module_files
            .join(db_tables.files)
            .select()
            .where(db_tables.module_files.c.module_ident == ident))
    result = db_engines['common'].execute(stmt).fetchall()
    files = {x.filename: x for x in result}
    assert book_cover.filename in files
    assert files[book_cover.filename].sha1 == book_cover.sha1
    assert files[book_cover.filename].file == book_cover.data.read()


def test_publish_revision_that_overwrites_existing_resources(
        content_util, persist_util, app, db_engines, db_tables):
    # Insert initial collection and modules.
    resources = list([content_util.gen_resource() for x in range(0, 2)])

    # Create a book-cover resource
    book_cover_filename = 'book-cover.png'
    book_cover_media_type = 'image/png'
    book_cover_img = generate_random_image_by_size(10)
    book_cover_data = io.BytesIO()
    book_cover_img.save(book_cover_data, 'PNG')
    book_cover_data.seek(0)
    book_cover = content_util.gen_resource(
        data=book_cover_data,
        filename=book_cover_filename,
        media_type=book_cover_media_type,
    )
    resources.append(book_cover)

    collection, tree, modules = content_util.gen_collection(
        resources=resources
    )
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)
    metadata = parse_collection_metadata(collection)

    # Overide the existing book-cover resource
    new_book_cover_img = generate_random_image_by_size(10)
    new_book_cover_data = io.BytesIO()
    new_book_cover_img.save(new_book_cover_data, 'PNG')
    new_book_cover_data.seek(0)
    new_book_cover = content_util.gen_resource(
        data=new_book_cover_data,
        filename=book_cover_filename,
        media_type=book_cover_media_type,
    )
    collection.resources.pop()  # pop off the old book-cover
    collection.resources.append(new_book_cover)
    assert book_cover.sha1 != new_book_cover.sha1

    # Collect control data for this current version
    stmt = (
        db_tables.module_files
        .join(db_tables.files)
        .select()
        .where(db_tables.modules.c.moduleid == metadata.id)
    )
    control_data = db_engines['common'].execute(stmt).fetchall()

    # Ensure the replaced resource really was in the content
    # prior to our publication
    control_files = {x.filename: x for x in control_data}
    replaced_file_record = control_files[book_cover_filename]
    assert replaced_file_record.sha1 == book_cover.sha1
    assert replaced_file_record.file == book_cover.data.read()
    book_cover.data.seek(0)

    # TARGET
    with db_engines['common'].begin() as conn:
        (id, version), ident = publish_legacy_book(
            collection,
            metadata,
            ('user1', 'test publish',),
            conn,
        )

    # Check for file insertion
    stmt = (db_tables.module_files
            .join(db_tables.files)
            .select()
            .where(db_tables.module_files.c.module_ident == ident))
    result = db_engines['common'].execute(stmt).fetchall()
    files = {x.filename: x for x in result}
    assert new_book_cover.filename in files
    assert files[new_book_cover.filename].sha1 == new_book_cover.sha1
    assert files[new_book_cover.filename].file == new_book_cover.data.read()
