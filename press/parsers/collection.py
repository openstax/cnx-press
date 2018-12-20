from xml import sax
from press.models import CollectionMetadata, PressElement
from .common import make_cnx_xpath, make_elm_tree, parse_common_properties


def nsmap_reversed(nsmap):
    return {y: x for x, y in nsmap.items()}


def parse_collection_metadata(model):
    """Parse the metadata from the given object.

    :param model: the object to parse
    :type model: :class:`litezip.Collection`
    :returns: a metadata object
    :rtype: :class:`press.models.CollectionMetadata`

    """
    elm_tree = make_elm_tree(model)
    xpath = make_cnx_xpath(elm_tree)

    props = parse_common_properties(elm_tree)

    print_style = xpath('//col:param[@name="print-style"]/@value')
    if not print_style or not print_style[0]:
        props['print_style'] = None
    else:
        props['print_style'] = print_style[0]

    return CollectionMetadata(**props)


class CollectionXmlHandler(sax.ContentHandler):
    def __init__(self, root):
        self.current_node = root
        self.next_node = None

    def startElementNS(self, name, qname, attrs):
        uri, localname = name
        # nsmap = nsmap_reversed(COLLECTION_NSMAP)
        # name_str = '{}:{}'.format(nsmap[uri], localname)

        # TODO: pass in the URI and have the model map it to a namespace.
        self.next_node = PressElement(localname,
                                      self._attrs_no_uri(attrs))

        # self.next_node = PressElement(name_str, self._attrs_no_uri(attrs))
        self.current_node.add_child(self.next_node)
        self.current_node = self.next_node

    def characters(self, content):
        # We have to create a new node so that the __hash__() is re-calculated
        new_node = self.current_node.insert_text(content)
        new_node.parent = self.current_node.parent
        new_node.children = self.current_node.children
        # AND the parent needs to contain the new child element for the old one
        self.current_node.parent.children.pop()
        self.current_node.parent.children.append(new_node)
        # And finally:
        self.current_node = new_node

    def endElementNS(self, name, qname):
        self.current_node = self.current_node.parent

    def _attrs_no_uri(self, attrs):
        return {name: value for (uri, name), value in attrs.items()}


def parse_collxml(input_collxml):
    """
    Given a collxml document, parses the document to a python object
    where collections and sub-collections (both branching points) contain
    subcollections and modules (leaf nodes).
    """
    tree_root = PressElement('root')

    parser = sax.make_parser()
    parser.setFeature(sax.handler.feature_namespaces, 1)
    parser.setContentHandler(CollectionXmlHandler(tree_root))


    # adds the ability to parse an obj that comes from the DB
    if isinstance(input_collxml, memoryview):
        import io
        input_collxml = io.BytesIO(input_collxml)


    parser.parse(input_collxml)  # parse a file-like object

    return tree_root
