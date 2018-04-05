from sqlalchemy.sql import text


__all__ = (
    'bump_version',
    'get_previous_published_version',
)


def bump_version(trans, uuid, is_minor_bump=False):
    """Bump to the next version for the given content identified
    by ``uuid``.

    If ``is_minor_bump`` is ``True`` the version will minor bump. That is
    1.2 becomes 1.3 in the case of Collections. And 2 becomes 3 for
    Modules regardless of this option.

    :param trans: the database transaction
    :param uuid: uuid of the content
    :param is_minor_bump: designate whether this is a minor version increase
    :type is_minor_bump: bool
    :returns: the next available version as a version tuple
              containing major and minor version.
    :rtypes: tuple
    """
    stmt = (text('SELECT portal_type, major_version, minor_version '
                 'FROM latest_modules '
                 'WHERE uuid = :uuid ::uuid')
            .bindparams(uuid=uuid))
    result = trans.execute(stmt)
    type_, major_version, minor_version = result.fetchone()
    incr = 1
    if type_ == 'Collection' and is_minor_bump:
        minor_version = minor_version + incr
    else:
        major_version = major_version + incr
    return (major_version, minor_version,)


def get_previous_published_version(trans, uuid, version):
    """Get the version of the previously published content
    at ``uuid`` and ``version```.

    :param trans: the database transaction
    :param uuid: uuid of the content
    :param version: a tuple of major and minor version values
    :type version: tuple([int, int])
    :returns: the previous published version as a version tuple
              containing major and minor version.
    :rtypes: tuple([int, int])

    """
    (major_version, minor_version) = version
    stmt = (text('WITH contextual_module AS ( '
                 'SELECT module_ident '
                 'FROM modules '
                 'WHERE uuid = :uuid '
                 '  AND major_version = :major_version '
                 '  AND minor_version = :minor_version '
                 ') '
                 'SELECT m.major_version, m.minor_version '
                 'FROM modules AS m '
                 '  JOIN contextual_module AS context '
                 '    ON (m.uuid = context.uuid) '
                 'WHERE m.module_ident < context.module_ident '
                 'ORDER BY revised DESC '
                 'LIMIT 1')
            .bindparams(uuid=uuid,
                        major_version=major_version,
                        minor_version=minor_version))
    result = trans.execute(stmt)
    try:
        (major_version, minor_version) = result.fetchone()
    except TypeError:  # NoneType
        (major_version, minor_version) = (None, None)
    return (major_version, minor_version)
