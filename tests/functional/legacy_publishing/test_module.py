import pytest

from datetime import timedelta

from dateutil.parser import parse as parse_date
from litezip.main import COLLECTION_NSMAP

from press.legacy_publishing.module import (
    publish_legacy_page,
)
from press.parsers import (
    parse_module_metadata,
)

from press.errors import Unchanged

from tests.conftest import GOOGLE_ANALYTICS_CODE
from tests.helpers import element_tree_from_model


def test_publish_revision(
        content_util, persist_util, app, db_engines, db_tables):
    resources = list([content_util.gen_resource() for x in range(0, 2)])
    module = content_util.gen_module(resources=resources)
    module = persist_util.insert_module(module)

    metadata = parse_module_metadata(module)

    # Collect control data for non-legacy metadata
    stmt = (
        db_tables.modules.select()
        .where(db_tables.modules.c.moduleid == metadata.id)
    )
    control_metadata = db_engines['common'].execute(stmt).fetchone()

    # TARGET
    with pytest.raises(Unchanged), db_engines['common'].begin() as conn:
        now = conn.execute('SELECT CURRENT_TIMESTAMP as now').fetchone().now
        (id, version), ident = publish_legacy_page(
            module,
            metadata,
            ('user1', 'test publish',),
            conn,
        )

    # Change the module text, to make it publishable.
    index_cnxml = module.file.read_text()
    start_offset = index_cnxml.find('test document')
    module.file.write_text(index_cnxml[:start_offset] +
                           'TEST DOCUMENT' +
                           index_cnxml[start_offset + 13:])

    # TARGET - again
    with db_engines['common'].begin() as conn:
        now = conn.execute('SELECT CURRENT_TIMESTAMP as now').fetchone().now
        (id, version), ident = publish_legacy_page(
            module,
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
    assert result.version == '1.2'
    assert result.uuid == control_metadata.uuid
    assert result.major_version == 2
    assert result.minor_version is None
    # Check for reuse of the existing abstract
    assert result.abstractid == control_metadata.abstractid
    assert result.created == parse_date(metadata.created)
    assert result.revised == now
    assert result.portal_type == 'Module'
    assert result.name == metadata.title
    assert result.licenseid == 13
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
    files = {x.filename: x for x in result}
    assert len(files) == len(resources) + 2  # content files
    assert 'index.cnxml' in files
    assert 'index.cnxml.html' in files

    # Check for resource file insertion
    html_content = files['index.cnxml.html'].file.decode('utf8')
    for resource in resources:
        assert resource.filename in files
        # Check for reference rewrites in the content. This is out of scope
        # for this project, but order of insertion matters in order for
        # the references to be rewritten.
        assert '/resources/{}'.format(resource.sha1) in html_content


def test_publish_revision_with_new_abstract(
        content_util, persist_util, app, db_engines, db_tables):
    resources = list([content_util.gen_resource() for x in range(0, 2)])
    module = content_util.gen_module(resources=resources)
    module = persist_util.insert_module(module)

    with element_tree_from_model(module) as xml:
        elm = xml.xpath('//md:abstract', namespaces=COLLECTION_NSMAP)[0]
        elm.text += ' -- appendage'

    metadata = parse_module_metadata(module)

    # Collect control data for non-legacy metadata
    stmt = (
        db_tables.modules.select()
        .where(db_tables.modules.c.moduleid == metadata.id)
    )
    control_metadata = db_engines['common'].execute(stmt).fetchone()

    # TARGET
    with db_engines['common'].begin() as conn:
        (id, version), ident = publish_legacy_page(
            module,
            metadata,
            ('user1', 'test publish',),
            conn,
        )

    # Check for a new abstract insertion
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
    resources = list([content_util.gen_resource() for x in range(0, 2)])
    module = content_util.gen_module(resources=resources)
    module = persist_util.insert_module(module)

    with element_tree_from_model(module) as xml:
        elm = xml.xpath('//md:created', namespaces=COLLECTION_NSMAP)[0]
        actual_created = parse_date(elm.text)
        changed_created = actual_created - (timedelta(days=365) * 8)
        elm.text = changed_created.isoformat()

    metadata = parse_module_metadata(module)

    # Collect control data for non-legacy metadata
    stmt = (
        db_tables.modules.select()
        .where(db_tables.modules.c.moduleid == metadata.id)
    )
    control_metadata = db_engines['common'].execute(stmt).fetchone()
    assert control_metadata.created == actual_created

    # TARGET
    with db_engines['common'].begin() as conn:
        (id, version), ident = publish_legacy_page(
            module,
            metadata,
            ('user1', 'test publish',),
            conn,
        )

    # Check for a new abstract insertion
    stmt = (
        db_tables.modules
        .select()
        .where(db_tables.modules.c.module_ident == ident)
    )
    result = db_engines['common'].execute(stmt).fetchone()
    assert result.created == control_metadata.created
    assert result.created != changed_created


def test_publish_revision_that_is_derived(
        content_util, persist_util, app, db_engines, db_tables):
    resources = list([content_util.gen_resource() for x in range(0, 2)])
    module = content_util.gen_module(resources=resources)
    module = persist_util.insert_module(module)

    metadata = parse_module_metadata(module)

    # Derive a copy of the collection
    derived_module = persist_util.derive_from(module)
    derived_metadata = parse_module_metadata(derived_module)

    # Collect control data for non-legacy metadata
    stmt = (
        db_tables.modules.select()
        .where(db_tables.modules.c.moduleid == derived_metadata.id)
    )
    control_metadata = db_engines['common'].execute(stmt).fetchone()

    # Change the module text, to make it publishable.
    index_cnxml = derived_module.file.read_text()
    start_offset = index_cnxml.find('test document')
    derived_module.file.write_text(index_cnxml[:start_offset] +
                                   'TEST DOCUMENT' +
                                   index_cnxml[start_offset + 13:])

    # TARGET
    with db_engines['common'].begin() as conn:
        now = conn.execute('SELECT CURRENT_TIMESTAMP as now').fetchone().now
        (id, version), ident = publish_legacy_page(
            derived_module,
            derived_metadata,
            ('user1', 'test publish',),
            conn,
        )

    # Lookup parent's metadata (ident and authors)
    # for parentage checks against the derived-copy metadata.
    stmt = (
        db_tables.latest_modules
        .select()
        .where(db_tables.latest_modules.c.moduleid == module.id)
    )
    parent_metadata_result = db_engines['common'].execute(stmt).fetchone()

    # Check core metadata insertion
    stmt = (
        db_tables.modules.join(db_tables.abstracts)
        .select()
        .where(db_tables.modules.c.module_ident == ident)
    )
    result = db_engines['common'].execute(stmt).fetchone()
    assert result.version == '1.2'
    assert result.uuid == control_metadata.uuid
    assert result.major_version == 2
    assert result.minor_version is None
    assert result.abstract == derived_metadata.abstract
    assert result.created == parse_date(metadata.created)
    assert result.revised == now
    assert result.portal_type == 'Module'
    assert result.name == derived_metadata.title
    assert result.licenseid == 13
    assert result.submitter == 'user1'
    assert result.submitlog == 'test publish'
    assert result.authors == list(derived_metadata.authors)
    assert result.maintainers == list(derived_metadata.maintainers)
    assert result.licensors == list(derived_metadata.licensors)
    assert result.google_analytics == GOOGLE_ANALYTICS_CODE

    # Check for derived metadata (parent and parent authors)
    assert result.parent == parent_metadata_result.module_ident
    assert result.parentauthors == parent_metadata_result.authors

    # Check for file insertion
    stmt = (
        db_tables.module_files
        .join(db_tables.files)
        .select()
        .where(db_tables.module_files.c.module_ident == ident)
        .where(db_tables.module_files.c.filename == 'index.cnxml')
    )
    module_doc = db_engines['common'].execute(stmt).fetchone()
    expected = bytes(
        ('<md:derived-from url="http://cnx.org/content/{}/{}"/>'
         .format(metadata.id, metadata.version)),
        'utf-8',
    )
    assert expected in module_doc.file


def test_publish_revision_with_new_resources(
        content_util, persist_util, app, db_engines, db_tables):
    resources = list([content_util.gen_resource() for x in range(0, 2)])
    module = content_util.gen_module(resources=resources)
    module = persist_util.insert_module(module)

    # Add a new resouce to the module
    new_resource = content_util.gen_resource()
    module.resources.append(new_resource)

    metadata = parse_module_metadata(module)

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
    assert new_resource.filename not in control_files

    # TARGET
    with db_engines['common'].begin() as conn:
        (id, version), ident = publish_legacy_page(
            module,
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
    assert new_resource.filename in files
    assert files[new_resource.filename].sha1 == new_resource.sha1
    assert files[new_resource.filename].file == new_resource.data.read_bytes()


def test_publish_revision_that_overwrites_existing_resources(
        content_util, persist_util, app, db_engines, db_tables):
    resources = list([content_util.gen_resource() for x in range(0, 2)])
    module = content_util.gen_module(resources=resources)
    module = persist_util.insert_module(module)

    # Replace an existing resource with new file contents the module
    replaced_resource = module.resources.pop()
    new_resource = content_util.gen_resource(
        filename=replaced_resource.filename,
    )
    module.resources.append(new_resource)
    assert replaced_resource.filename == new_resource.filename

    metadata = parse_module_metadata(module)

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
    replaced_file_record = control_files[replaced_resource.filename]
    assert replaced_file_record.sha1 == replaced_resource.sha1
    assert replaced_file_record.file == replaced_resource.data.read_bytes()

    # TARGET
    with db_engines['common'].begin() as conn:
        (id, version), ident = publish_legacy_page(
            module,
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
    assert new_resource.filename in files
    assert files[new_resource.filename].sha1 == new_resource.sha1
    assert files[new_resource.filename].file == new_resource.data.read_bytes()
