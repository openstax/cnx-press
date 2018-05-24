from litezip.main import COLLECTION_NSMAP
from lxml import etree

from ..utils import convert_version_to_legacy_version


__all__ = (
    'replace_id_and_version',
)


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
        fb.write(etree.tostring(xml))
