from press.parsers import parse_collxml


__all__ = (
    'convert_to_legacy_domain',
    'convert_version_tuple_to_version_string',
    'convert_version_to_legacy_version',
    'requires_major_version_update',
)


def requires_major_version_update(before, after):
    """Tests whether or not a collection changed.
    If one did, it requires a major version update, so True will be returned.
    """
    with open(before, 'rb') as file1:
        tree1 = parse_collxml(file1)

    with open(after, 'rb') as file2:
        tree2 = parse_collxml(file2)

    for sub_tree_1, sub_tree_2 in zip(tree1.traverse(), tree2.traverse()):
        if not sub_tree_1.is_equal_to(sub_tree_2):
            return True
    return False


def convert_version_tuple_to_version_string(version):
    """Converts a version tuple to a version string.

    :param version: content's major and minor version
    :type version: tuple of int

    """
    return '.'.join([str(vv) for vv in version if vv])


def convert_version_to_legacy_version(version):
    """Converts a version to a legacy version.

    :param version: content's major and minor version
    :type version: tuple of int

    """
    return '1.{}'.format(version[0])


def convert_to_legacy_domain(domain):
    """Given the existing domain, convert it to the legacy domain."""
    sep = len(domain.split('.')) > 2 and '-' or '.'
    return 'legacy{}{}'.format(sep, domain)
