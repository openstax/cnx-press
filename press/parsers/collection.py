from press.models import CollectionMetadata
from .common import make_cnx_xpath, make_elm_tree, parse_common_properties


def parse_collection_metadata(model):
    """Given a Collection (``litezip.Collection``), parse out the metadata.
    Return a CollectionMetadata object (``press.models.CollectionMetadata``).

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
