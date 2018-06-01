__all__ = (
    'convert_to_legacy_domain',
    'convert_version_to_legacy_version',
)


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
