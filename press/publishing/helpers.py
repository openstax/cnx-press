from sqlalchemy.sql import text


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
