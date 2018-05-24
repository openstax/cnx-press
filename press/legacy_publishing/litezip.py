from litezip.main import COLLECTION_NSMAP
from lxml import etree

from litezip import Collection, Module

from press.parsers import parse_collection_metadata, parse_module_metadata

from .collection import publish_legacy_book
from .module import publish_legacy_page
from ..utils import convert_version_to_legacy_version


__all__ = (
    'publish_litezip',
)


def publish_litezip(struct, submission, db_conn):
    """Publish the contents of a litezip structured set of data.

    :param struct: a litezip struct from (probably from
                   :func:`litezip.parse_litezip`)
    :param submission: a two value tuple containing a userid
                       and submit message
    :type submission: tuple
    :param db_conn: a database connection object
    :type db_conn: :class:`sqlalchemy.engine.Connection`

    """
    # Dissect objects from litezip struct.
    try:
        collection = [x for x in struct if isinstance(x, Collection)][0]
    except IndexError:  # pragma: no cover
        raise NotImplementedError('litezip without collection')
    id_map = {}

    # Parse Collection tree to update the newly published Modules.
    with collection.file.open('rb') as fb:
        xml = etree.parse(fb)

    # Publish the Modules.
    for module in [x for x in struct if isinstance(x, Module)]:
        metadata = parse_module_metadata(module)
        old_id = module.id
        (id, version), ident = publish_legacy_page(module, metadata,
                                                   submission, db_conn)
        id_map[old_id] = (id, version)
        # Update the Collection tree
        xpath = '//col:module[@document="{}"]'.format(old_id)
        for elm in xml.xpath(xpath, namespaces=COLLECTION_NSMAP):
            elm.attrib['document'] = id
            version_attrib_name = (
                '{{{}}}version-at-this-collection-version'
                .format(COLLECTION_NSMAP['cnxorg']))
            legacy_version = convert_version_to_legacy_version(version)
            elm.attrib[version_attrib_name] = legacy_version

    # Rebuild the Collection tree from the newly published Modules.
    with collection.file.open('wb') as fb:
        fb.write(etree.tostring(xml))

    # Publish the Collection.
    metadata = parse_collection_metadata(collection)
    old_id = collection.id
    (id, version), ident = publish_legacy_book(collection, metadata,
                                               submission, db_conn)
    id_map[old_id] = (id, version)

    return id_map
