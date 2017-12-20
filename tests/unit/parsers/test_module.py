from litezip import parse_module
from press.parsers import parse_module_metadata


def test_parse_module_metadata(litezip_valid_litezip):
    module_id = 'm37154'
    # given a Module object,
    model = parse_module(litezip_valid_litezip / module_id)
    # parse the metadata into a CollectionMetadata,
    md = parse_module_metadata(model)
    # which we then test for data point information

    assert md.id == module_id
    assert md.version == '1.2'
    assert md.created == '2010/08/09 14:25:38 -0500'
    assert md.revised == '2011/03/08 18:15:08 -0600'
    assert md.title == ('A Student to Student Intro to IDE Programming '
                        'and CCS4')
    assert md.license_url == 'http://creativecommons.org/licenses/by/3.0/'
    assert md.language == 'en'

    assert md.authors == ('mwjhnsn', 'ww2')
    assert md.maintainers == ('mwjhnsn', 'ww2')
    assert md.licensors == ('mwjhnsn', 'ww2')

    assert md.keywords == (
        'CCSv4',
        'Code Composer Studio',
        'ELEC 220',
        'IDE',
        'MSP 430',
    )
    assert md.subjects == ('Science and Technology',)

    assert md.abstract == ("A basic introduction to how to write "
                           "and debug programs in Code Composer Studio V4.")
