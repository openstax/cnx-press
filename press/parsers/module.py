from press.models import ModuleMetadata
from .common import make_elm_tree, parse_common_properties


def parse_module_metadata(model):
    """Parse the metadata from the given object.

    :param model: the object to parse
    :type model: :class:`litezip.Module`
    :returns: a metadata object
    :rtype: :class:`press.models.ModuleMetadata`

    """
    return ModuleMetadata(**parse_common_properties(make_elm_tree(model)))
