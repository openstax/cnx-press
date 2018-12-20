from pathlib import Path

from litezip import parse_collection
from litezip.main import COLLECTION_NSMAP
from lxml import etree

from press.parsers import parse_collection_metadata, parse_collxml
from press.models import PressElement


def test_parse_collxml(collxml_templates):
    with (collxml_templates / 'original.xml').open() as origin:
        tree = parse_collxml(origin)
    assert len(tuple(tree.iter())) == 83
    assert isinstance(tree, PressElement)
    assert tree.tag == 'root'


def test_parse_collection_metadata(litezip_valid_litezip):
    # given a Collection object,
    model = parse_collection(litezip_valid_litezip)
    # parse the metadata into a CollectionMetadata,
    md = parse_collection_metadata(model)
    # which we then test for data point information

    assert md.id == 'col11405'
    assert md.version == '1.2'
    assert md.created == '2011/05/24 10:31:56.888 GMT-5'
    assert md.revised == '2013/03/11 22:52:33.244 GMT-5'
    assert md.title == 'Intro to Computational Engineering: Elec 220 Labs'
    assert md.license_url == 'http://creativecommons.org/licenses/by/3.0/'
    assert md.language == 'en'

    assert md.authors == ('mwjhnsn', 'jedifan42')
    assert md.maintainers == ('mwjhnsn', 'jedifan42', 'cavallar')
    assert md.licensors == ('mwjhnsn', 'jedifan42', 'cavallar')

    assert md.keywords == (
        'Calculator',
        'Cavallaro',
        'Elec 220',
        'Gate',
        'Interrupt',
        'LC-3',
        'Loop',
        'Microcontroller',
        'MSP 430',
        'Rice',
    )
    assert md.subjects == ('Science and Technology',)

    assert md.abstract == ("This collection houses all the documentation "
                           "for the lab component of Rice Universities Elec "
                           "220 lab component.  The labs cover topics such "
                           "as gates, simulation, basic digital I/O, "
                           "interrupt driven embedded programming, C "
                           "language programming, and finally a/d "
                           "interfacing and touch sensors.")
    # This test case uses ``value=""`` in the xml, so a value is found.
    assert md.print_style is None


def test_parse_colletion_metdata_without_print_style(tmpdir,
                                                     litezip_valid_litezip):
    working_dir = tmpdir.mkdir('col')
    collection_file = working_dir.join('collection.xml')
    # Copy over and modify the collection.xml file.
    with (litezip_valid_litezip / 'collection.xml').open() as origin:
        xml = etree.parse(origin)
        elm = xml.xpath('//col:param[@name="print-style"]',
                        namespaces=COLLECTION_NSMAP)[0]
        elm.getparent().remove(elm)
        collection_file.write(etree.tounicode(xml).encode('utf8'))
    assert 'print-style' not in collection_file.read()

    # Test the parser doesn't error when a print-style is missing.
    # given a Collection object,
    model = parse_collection(Path(working_dir))
    # parse the metadata into a CollectionMetadata,
    md = parse_collection_metadata(model)
    assert md.print_style is None


def test_parse_colletion_metdata_with_print_style(tmpdir,
                                                  litezip_valid_litezip):
    specific_print_style = 'woodblock'

    working_dir = tmpdir.mkdir('col')
    collection_file = working_dir.join('collection.xml')
    # Copy over and modify the collection.xml file.
    with (litezip_valid_litezip / 'collection.xml').open() as origin:
        xml = etree.parse(origin)
        elm = xml.xpath('//col:param[@name="print-style"]',
                        namespaces=COLLECTION_NSMAP)[0]
        elm.attrib['value'] = specific_print_style
        collection_file.write(etree.tounicode(xml).encode('utf8'))

    # Test the parser doesn't error when a print-style is missing.
    # given a Collection object,
    model = parse_collection(Path(working_dir))
    # parse the metadata into a CollectionMetadata,
    md = parse_collection_metadata(model)
    assert md.print_style == specific_print_style
