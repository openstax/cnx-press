from press.legacy_publishing.utils import (
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
