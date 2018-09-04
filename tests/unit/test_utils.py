from press.utils import (
    convert_to_legacy_domain,
    convert_version_to_legacy_version,
    requires_major_version_update,
)


def test_major_version_checker(litezip_valid_litezip):
    dir_to_file = (litezip_valid_litezip / 'collection.xml')
    assert requires_major_version_update(dir_to_file, dir_to_file) is False


def test_a_change_in_mod_title_req_major_change():
    """A change in a module's title requires a major version update.
    """
    # TODO: locate a before and after collxml files.


def test_a_change_in_the_order_of_mods_req_maj_ver_updt():
    """A change in the order of modules requires a major version update.
    """
    # TODO: locate a before and after collxml files.


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
