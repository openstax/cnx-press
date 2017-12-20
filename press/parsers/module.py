from functools import partial

from lxml import etree
from litezip.main import COLLECTION_NSMAP

from press.models import ModuleMetadata


def parse_module_metadata(model):
    """Given a Module (``litezip.Module``), parse out the metadata.
    Return a ModuleMetadata object (``press.models.ModuleMetadata``).

    """
    elm_tree = etree.parse(model.file.open())
    xpath = partial(elm_tree.xpath, namespaces=COLLECTION_NSMAP)
    role_xpath = lambda xp: tuple(xpath(xp)[0].split())  # noqa: E731

    props = {
        'id': xpath('//md:content-id/text()')[0],
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
        'abstract': xpath('//md:abstract/text()')[0],
    }

    # Note, Press does not parse or update user (aka "actor" in the xml)
    # information. This should be done directly using the "legacy" software.

    return ModuleMetadata(**props)
