from dateutil.parser import parse as parse_date

from press.legacy_publishing.module import (
    publish_legacy_page,
)
from press.parsers import (
    parse_module_metadata,
)


def test_publish_revision_to_legacy_page(
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

    with db_engines['common'].begin() as conn:
        (id, version), ident = publish_legacy_page(
            module,
            metadata,
            ('user1', 'test publish',),
            conn,
        )

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
    assert len(filenames) == len(resources) + 2  # content files
    assert 'index.cnxml' in filenames
    assert 'index.cnxml.html' in filenames
    # Check for resource file insertion
    for resource in resources:
        assert resource.filename in filenames
