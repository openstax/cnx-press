import hashlib
from pathlib import Path

from press.utils import (
    convert_to_legacy_domain,
    convert_version_to_legacy_version,
    produce_hashes_from_filepath,
)

from tests.random_image import (
    generate_image_by_output_size,
    generate_random_image_by_size,
    save_image,
)


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


class TestProduceHashesFromFilepath:

    def get_sha1(self, filepath):
        sha1 = hashlib.sha1()
        with filepath.open('rb') as fb:
            sha1.update(fb.read())
        return sha1.hexdigest()

    def get_md5(self, filepath):
        md5 = hashlib.md5()
        with filepath.open('rb') as fb:
            md5.update(fb.read())
        return md5.hexdigest()

    def test(self, tmpdir):
        filepath = Path(tmpdir.mkdir('img')) / 'file.jpeg'

        img = generate_random_image_by_size(10)
        save_image(img, str(filepath))

        hashes = produce_hashes_from_filepath(filepath)

        expected = {
            'sha1': self.get_sha1(filepath),
            'md5': self.get_md5(filepath),
        }
        assert hashes == expected

    def test_large_file(self, tmpdir):
        filepath = Path(tmpdir.mkdir('img')) / 'big_file.jpeg'

        img = generate_image_by_output_size(10240)
        save_image(img, str(filepath))

        hashes = produce_hashes_from_filepath(filepath)

        expected = {
            'sha1': self.get_sha1(filepath),
            'md5': self.get_md5(filepath),
        }
        assert hashes == expected
