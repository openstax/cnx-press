from press.models import ModuleMetadata
from .common import make_elm_tree, parse_common_properties


def parse_module_metadata(model):
    """Given a Module (``litezip.Module``), parse out the metadata.
    Return a ModuleMetadata object (``press.models.ModuleMetadata``).

    """
    return ModuleMetadata(**parse_common_properties(make_elm_tree(model)))
