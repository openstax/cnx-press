from litezip import (
    Collection,
    Module,
)
from litezip.main import COLLECTION_NSMAP
from lxml import etree

from ..utils import convert_version_to_legacy_version

__all__ = (
    'replace_derived_from',
    'replace_id_and_version',
    'needs_major_rev',
    'needs_minor_rev'
)


def needs_major_rev(pre, post):
    """True if:
    - Collection title changes (this does not include module title changes)
    - Collection structure changes (adding, removing, moving)
    """
    removed = set(pre.iter('module')) - set(post.iter('module'))
    added = set(post.iter('module')) - set(pre.iter('module'))

    if len(removed) != 0 or len(added) != 0:
        return True  # number of modules changed

    if pre.find('title').alltext() != post.find('title').alltext():
        return True  # collection's title changed

    for this, other in zip(pre.find('content').iter(),
                           post.find('content').iter()):
        if this != other:
            return True  # order changed

    return False


def needs_minor_rev(pre, post):
    """True if:
    1. Collection or module metadata changes
        - abstract
        - subject
    2. Parameter changes
    3. Collection or module actor changes
    3. Collection or module role changes
    """
    if pre.find('abstract') != post.find('abstract'):
        return True
    if pre.find('subjectlist').alltext() != post.find('subjectlist').alltext():
        return True

    params_before = params_as_dict(pre.findall('param'))
    params_after = params_as_dict(post.findall('param'))

    if params_before != params_after:
        return True

    actors_before = actors_as_dict(pre.findall('person'))
    actors_after = actors_as_dict(post.findall('person'))

    if actors_before != actors_after:
        return True

    roles_before = roles_as_dict(pre.findall('role'))
    roles_after = roles_as_dict(post.findall('role'))

    if roles_before != roles_after:
        return True

    return False


def params_as_dict(params):
    params_dict = dict()

    for p in params:
        k = p.attrs['name']
        v = p.attrs['value']
        params_dict[k] = v
    return params_dict


def actors_as_dict(persons):
    actors_dict = dict()

    for p in persons:
        actors_dict[p.firstname] = p.firstname.text
        actors_dict[p.surname] = p.surname.text
        actors_dict[p.fullname] = p.fullname.text
    return actors_dict


def roles_as_dict(roles):
    authors_dict = dict()

    for r in roles:
        for k, v in r.attrs.items():
            authors_dict[r.attrs['type']] = set(r.text.split(' '))
    return authors_dict


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
