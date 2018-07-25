from press.legacy_publishing.utils import (
    replace_derived_from,
    replace_id_and_version,
)


def test_replace_id_and_version(content_util):
    module = content_util.gen_module()
    id = '$$$_id_$$$'
    version = ('$', '%',)

    # Call the target
    replace_id_and_version(module, id, version)

    # Check the id and version were replaced
    with module.file.open('r') as fb:
        text = fb.read()
    assert id in text
    assert '1.{}'.format(version[0]) in text


class TestReplaceDerivedFrom:

    def test_create(self, content_util):
        module = content_util.gen_module()
        id = '$$$_id_$$$'
        version = '$.%'
        url = 'http://cnx.org/content/{}/{}'.format(id, version)

        # Call the target
        replace_derived_from(module, url)

        # Check the derived-from was replaced
        with module.file.open('r') as fb:
            text = fb.read()
        expected = '<md:derived-from url="{}"/>'.format(url)
        assert expected in text

    def test_replace(self, content_util):
        original_module = content_util.gen_module()
        module = content_util.gen_module(derived_from=original_module)
        id = '$$$_id_$$$'
        version = '$.%'

        url = 'http://cnx.org/content/{}/{}'.format(id, version)

        # Call the target
        replace_derived_from(module, url)

        # Check the derived-from was replaced
        with module.file.open('r') as fb:
            text = fb.read()
        expected = '<md:derived-from url="{}"/>'.format(url)
        assert expected in text
