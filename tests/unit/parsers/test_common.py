from litezip.main import COLLECTION_NSMAP
from lxml import etree

from press.parsers.common import parse_common_properties


# https://github.com/Connexions/cnx-press/issues/17
def test_parse_common_properties_without_abstract(litezip_valid_litezip):
    # Copy over and modify the collection.xml file.
    with (litezip_valid_litezip / 'collection.xml').open() as origin:
        xml = etree.parse(origin)
        elm = xml.xpath('//md:abstract',
                        namespaces=COLLECTION_NSMAP)[0]
        elm.getparent().remove(elm)

        # Test the parser doesn't error when the abstract is missing.
        # given a ElementTree object,
        props = parse_common_properties(xml)
        # parse the metadata into a dict and check for the abstract.
        assert props['abstract'] is None


def test_parse_with_cnxml_abstract(litezip_valid_litezip):
    abstract_xml = ("<list><item>A</item>"
                    "<item>C</item><item>E</item>"
                    "</list>")
    # Copy over and modify the collection.xml file.
    with (litezip_valid_litezip / 'collection.xml').open() as origin:
        xml = etree.parse(origin)
        elm = xml.xpath('//md:abstract',
                        namespaces=COLLECTION_NSMAP)[0]
        elm.text = "FOO "
        abstract_elms = etree.fromstring(abstract_xml)
        abstract_elms.tail = " BAR"
        elm.append(abstract_elms)

        # Test the parser doesn't error when the abstract is missing.
        # given a ElementTree object,
        props = parse_common_properties(xml)

        expected_abstract = 'FOO {} BAR'.format(abstract_xml)
        # parse the metadata into a dict and check for the abstract.
        assert props['abstract'] == expected_abstract
