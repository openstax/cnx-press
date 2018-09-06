__all__ = (
    'convert_to_legacy_domain',
    'convert_version_tuple_to_version_string',
    'convert_version_to_legacy_version',
    'requires_major_version_update',
)


def requires_major_version_update(before, after):
    """Tests whether or not a collection changed.
    If one did, it requires a major version update and True will be returned.
    """
    for tree_before, tree_after in zip(before.traverse(), after.traverse()):
        if not tree_before.is_equal_to(tree_after):
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
