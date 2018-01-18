from functools import partial

from lxml import etree
from litezip.main import COLLECTION_NSMAP


__all__ = (
    'make_elm_tree',
    'make_cnx_xpath',
    'parse_common_properties',
)


def _maybe(l):
    """Grab the first value if it exists."""
    try:
        return l[0]
    except IndexError:
        return None


def make_elm_tree(model):
    """Makes an ElementTree from a litezip model (Collection or Module)."""
    with model.file.open() as fb:
        elm_tree = etree.parse(fb)
    return elm_tree


def make_cnx_xpath(elm_tree):
    """Makes an xpath function that includes the CNX namespaces."""
    return partial(elm_tree.xpath, namespaces=COLLECTION_NSMAP)


def parse_common_properties(elm_tree):
    """Given an ElementTree lookup the common and return the properties."""
    xpath = make_cnx_xpath(elm_tree)
    role_xpath = lambda xp: tuple(xpath(xp)[0].split())  # noqa: E731

    props = {
        'id': _maybe(xpath('//md:content-id/text()')),
        'version': xpath('//md:version/text()')[0],
        'created': xpath('//md:created/text()')[0],
        'revised': xpath('//md:revised/text()')[0],
        'title': xpath('//md:title/text()')[0],
        'license_url': xpath('//md:license/@url')[0],
        'language': xpath('//md:language/text()')[0],
        'authors': role_xpath('//md:role[@type="author"]/text()'),
        'maintainers': role_xpath('//md:role[@type="maintainer"]/text()'),
        'licensors': role_xpath('//md:role[@type="licensor"]/text()'),
        'keywords': tuple(xpath('//md:keywordlist/md:keyword/text()')),
        'subjects': tuple(xpath('//md:subjectlist/md:subject/text()')),
        'abstract': _maybe(xpath('//md:abstract/text()')),
    }

    # Note, Press does not parse or update user (aka "actor" in the xml)
    # information. This should be done directly using the "legacy" software.
    return props
