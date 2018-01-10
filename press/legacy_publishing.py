from litezip.main import COLLECTION_NSMAP
from lxml import etree
from sqlalchemy.sql import text


def publish_litezip(struct, registry):
    """\
    ``struct`` is a litezip struct from ``parse_litezip``
    ``registry`` is a pyramid component architecture registry

    """


def publish_legacy_page(model, metadata, submission, registry):
    """\
    ``model`` is a ``litezip.Module``
    ``metadata`` is a ``ModuleMetadata``
    ``submission`` is a two value tuple containing a userid and submit message
    ``registry`` is a pyramid component architecture registry

    """
    engine = registry.engines['common']
    t = registry.tables

    if model.id is None or metadata.id is None:  # pragma: no cover
        raise NotImplementedError()

    with engine.begin() as trans:
        result = trans.execute(
            t.latest_modules.select()
            .where(t.latest_modules.c.moduleid == metadata.id))
        # At this time, this code assumes an existing module
        existing_module = result.fetchone()
        version = tuple(int(x) for x in existing_module.version.split('.'))
        version = '.'.join([str(version[0]), str(version[1] + 1)])

        # Insert module metadata
        result = trans.execute(t.abstracts.insert()
                               .values(abstract=metadata.abstract))
        abstractid = result.inserted_primary_key[0]
        result = trans.execute(
            t.licenses.select()
            .where(t.licenses.c.url == metadata.license_url))
        licenseid = result.fetchone().licenseid
        result = trans.execute(t.modules.insert().values(
            moduleid=metadata.id,
            version=version,
            portal_type='Module',
            name=metadata.title,
            created=metadata.created,
            revised=metadata.revised,
            abstractid=abstractid,
            licenseid=licenseid,
            doctype='',
            submitter=submission[0],
            submitlog=submission[1],
            language=metadata.language,
            authors=metadata.authors,
            maintainers=metadata.maintainers,
            licensors=metadata.licensors,
            # TODO metadata does not currently capture parentage
            parent=None,
            parentauthors=None,
        ).returning(t.modules.c.module_ident, t.modules.c.moduleid))
        ident, id = result.fetchone()

        # Insert subjects metadata
        stmt = (text('INSERT INTO moduletags '
                     'SELECT :module_ident AS module_ident, tagid '
                     'FROM tags WHERE tag = any(:subjects)')
                .bindparams(module_ident=ident,
                            subjects=list(metadata.subjects)))
        result = trans.execute(stmt)

        # Insert keywords metadata
        stmt = (text('INSERT INTO keywords (word) '
                     'SELECT iword AS word '
                     'FROM unnest(:keywords ::text[]) AS iword '
                     '     LEFT JOIN keywords AS kw ON (kw.word = iword) '
                     'WHERE kw.keywordid IS NULL')
                .bindparams(keywords=list(metadata.keywords)))
        trans.execute(stmt)
        stmt = (text('INSERT INTO modulekeywords '
                     'SELECT :module_ident AS module_ident, keywordid '
                     'FROM keywords WHERE word = any(:keywords)')
                .bindparams(module_ident=ident,
                            keywords=list(metadata.keywords)))
        trans.execute(stmt)

        # Rewrite the content with the id and version
        with model.file.open('rb') as fb:
            xml = etree.parse(fb)
        elm = xml.xpath('//md:content-id', namespaces=COLLECTION_NSMAP)[0]
        elm.text = id
        elm = xml.xpath('//md:version', namespaces=COLLECTION_NSMAP)[0]
        elm.text = version
        with model.file.open('wb') as fb:
            fb.write(etree.tostring(xml))

        # Insert module files (content and resources)
        with model.file.open('rb') as fb:
            result = trans.execute(t.files.insert().values(
                file=fb.read(),
                media_type='text/xml',
            ))
        fileid = result.inserted_primary_key[0]
        result = trans.execute(t.module_files.insert().values(
            module_ident=ident,
            fileid=fileid,
            filename='index.cnxml',
        ))

        # TODO Insert resource files (images, pdfs, etc.)

    return ident


def publish_legacy_book(model, metadata, submission, registry):
    """\
    ``model`` is a ``litezip.Collection``
    ``metadata`` is a ``CollectionMetadata``
    ``submission`` is a two value tuple containing a userid and submit message
    ``registry`` is a pyramid component architecture registry

    """
    engine = registry.engines['common']
    t = registry.tables

    if model.id is None or metadata.id is None:  # pragma: no cover
        raise NotImplementedError()

    with engine.begin() as trans:
        result = trans.execute(
            t.modules.select()
            .where(t.modules.c.moduleid == metadata.id)
            .order_by(t.modules.c.major_version.desc())
            .limit(1))
        # At this time, this code assumes an existing module
        existing_module = result.fetchone()
        version = tuple(int(x) for x in existing_module.version.split('.'))
        version = '.'.join([str(version[0]), str(version[1] + 1)])

        # Insert module metadata
        result = trans.execute(t.abstracts.insert()
                               .values(abstract=metadata.abstract))
        abstractid = result.inserted_primary_key[0]
        result = trans.execute(
            t.licenses.select()
            .where(t.licenses.c.url == metadata.license_url))
        licenseid = result.fetchone().licenseid
        result = trans.execute(t.modules.insert().values(
            moduleid=metadata.id,
            version=version,
            portal_type='Collection',
            name=metadata.title,
            created=metadata.created,
            revised=metadata.revised,
            abstractid=abstractid,
            licenseid=licenseid,
            doctype='',
            submitter=submission[0],
            submitlog=submission[1],
            language=metadata.language,
            authors=metadata.authors,
            maintainers=metadata.maintainers,
            licensors=metadata.licensors,
            # TODO metadata does not currently capture parentage
            parent=None,
            parentauthors=None,
        ).returning(t.modules.c.module_ident, t.modules.c.moduleid))
        ident, id = result.fetchone()

        # Insert subjects metadata
        stmt = (text('INSERT INTO moduletags '
                     'SELECT :module_ident AS module_ident, tagid '
                     'FROM tags WHERE tag = any(:subjects)')
                .bindparams(module_ident=ident,
                            subjects=list(metadata.subjects)))
        result = trans.execute(stmt)

        # Insert keywords metadata
        stmt = (text('INSERT INTO keywords (word) '
                     'SELECT iword AS word '
                     'FROM unnest(:keywords ::text[]) AS iword '
                     '     LEFT JOIN keywords AS kw ON (kw.word = iword) '
                     'WHERE kw.keywordid IS NULL')
                .bindparams(keywords=list(metadata.keywords)))
        trans.execute(stmt)
        stmt = (text('INSERT INTO modulekeywords '
                     'SELECT :module_ident AS module_ident, keywordid '
                     'FROM keywords WHERE word = any(:keywords)')
                .bindparams(module_ident=ident,
                            keywords=list(metadata.keywords)))
        trans.execute(stmt)

        # Rewrite the content with the id and version
        with model.file.open('rb') as fb:
            xml = etree.parse(fb)
        elm = xml.xpath('//md:content-id', namespaces=COLLECTION_NSMAP)[0]
        elm.text = id
        elm = xml.xpath('//md:version', namespaces=COLLECTION_NSMAP)[0]
        elm.text = version
        with model.file.open('wb') as fb:
            fb.write(etree.tostring(xml))

        # Insert module files (content and resources)
        with model.file.open('rb') as fb:
            result = trans.execute(t.files.insert().values(
                file=fb.read(),
                media_type='text/xml',
            ))
        fileid = result.inserted_primary_key[0]
        result = trans.execute(t.module_files.insert().values(
            module_ident=ident,
            fileid=fileid,
            filename='collection.xml',
        ))

        # TODO Insert resource files (cover image, recipe, etc.)

    return ident
