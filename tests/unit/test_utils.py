from press.parsers import parse_collxml
from press.utils import (
    convert_to_legacy_domain,
    convert_version_to_legacy_version,
    requires_major_version_update,
)


def test_major_version_checker(collxml_templates):
    """No changes in collxml should NOT require a major version update.
    """
    with (collxml_templates / 'original.xml').open('r') as file:
        tree = parse_collxml(file)
    assert requires_major_version_update(tree, tree) is False


def test_a_change_in_title_req_major_change(collxml_templates):
    """A change in a module's title requires a major version update.
    """
    with (collxml_templates / 'original.xml').open('r') as before_doc, \
         (collxml_templates / 'changed_title.xml').open('r') as after_doc:
        tree_before = parse_collxml(before_doc)
        tree_after = parse_collxml(after_doc)

    assert requires_major_version_update(tree_before, tree_after) is True


def test_change_in_the_order_of_mods_req_maj_ver_update(collxml_templates):
    """A change in the order of modules requires a major version update.
    """
    with (collxml_templates / 'original.xml').open('r') as before_doc, \
         (collxml_templates / 'changed_order.xml').open('r') as after_doc:
        tree_before = parse_collxml(before_doc)
        tree_after = parse_collxml(after_doc)

    assert requires_major_version_update(tree_before, tree_after) is True


def test_change_in_title_markup_requires_maj_ver_update(collxml_templates):
    """Text surrounded by markup within titles is considered for equality.
    """
    diff_markup = 'changed_markup_in_title.xml'
    with (collxml_templates / 'markup_in_title.xml').open('r') as before_doc, \
         (collxml_templates / diff_markup).open('r') as after_doc:
        tree_before = parse_collxml(before_doc)
        tree_after = parse_collxml(after_doc)

    assert requires_major_version_update(tree_before, tree_after) is True


def test_module_version():
    version = (4, None)  # Note, modules do not have a minor version
    expected_version = '1.{}'.format(version[0])
    assert convert_version_to_legacy_version(version) == expected_version


def test_collection_version():
    version = (8, 11)
    expected_version = '1.{}'.format(version[0])
    assert convert_version_to_legacy_version(version) == expected_version


class TestConvertToLegacyDomain:

    def test_prod_domain(self):
        domain = 'example.com'
        expected = '.'.join(['legacy', domain])
        assert convert_to_legacy_domain(domain) == expected

    def test_dev_domain(self):
        domain = 'dev.example.com'
        expected = '-'.join(['legacy', domain])
        assert convert_to_legacy_domain(domain) == expected
