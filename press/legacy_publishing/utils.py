from litezip import (
    Collection,
    Module,
)
from litezip.main import COLLECTION_NSMAP
from lxml import etree

from ..utils import convert_version_to_legacy_version, \
    produce_hashes_from_filepath


__all__ = (
    'replace_derived_from',
    'replace_id_and_version',
    'produce_hashes_from_filepath',
)


def replace_derived_from(model, derived_from_url):
    """Does an inplace replacement or addition of the ``<md:derived-from>``
    tag.

    :param model: module
    :type model: :class:`litezip.Collection` or :class:`litezip.Module`
    :param derived_from_url: derived_from_url
    :type derived_from_url: str

    """
    with model.file.open('rb') as fb:
        xml = etree.parse(fb)
    namespace_prefix = {
        Module: 'c',
        Collection: 'col',
    }[type(model)]

    # Lookup the metadata element
    metadata_elm = xml.xpath(
        '//{}:metadata'.format(namespace_prefix),
        namespaces=COLLECTION_NSMAP,
    )[0]
    # Create the new derived-from element
    derived_from_elm = etree.fromstring(
        '<derived-from xmlns="{}" url="{}"/>'
        .format(
            COLLECTION_NSMAP['md'],
            derived_from_url,
        )
    )

    try:
        found_derived_from_elm = xml.xpath(
            '//md:derived-from',
            namespaces=COLLECTION_NSMAP,
        )[0]
    except IndexError:
        pass
    else:
        # Remove the element in favor of our newly created one
        metadata_elm.remove(found_derived_from_elm)
    finally:
        # Append the element to metadata
        metadata_elm.append(derived_from_elm)

    with model.file.open('wb') as fb:
        fb.write(etree.tounicode(xml).encode('utf8'))


def replace_id_and_version(model, id, version):
    """Does an inplace replacement of the given model's id and version

    :param model: module
    :type model: :class:`litezip.Collection` or :class:`litezip.Module`
    :param id: id
    :type id: str
    :param version: major and minor version tuple
    :type version: tuple of int

    """
    # Rewrite the content with the id and version
    with model.file.open('rb') as fb:
        xml = etree.parse(fb)
    elm = xml.xpath('//md:content-id', namespaces=COLLECTION_NSMAP)[0]
    elm.text = id
    elm = xml.xpath('//md:version', namespaces=COLLECTION_NSMAP)[0]
    elm.text = convert_version_to_legacy_version(version)
    with model.file.open('wb') as fb:
        fb.write(etree.tounicode(xml).encode('utf8'))
