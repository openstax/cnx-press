from sqlalchemy.sql import text

from .helpers import bump_version


__all__ = (
    'republish_collection',
)


_republish_tmplt = """\
WITH previous AS (
  SELECT module_ident
  FROM modules
WHERE uuid = :uuid
  AND major_version = :major_version
  AND minor_version = :minor_version
),
inserted AS (
  INSERT INTO modules
    (uuid, major_version, minor_version, revised,
     portal_type, moduleid,
     name, created, language,
     submitter, submitlog,
     abstractid, licenseid, parent, parentauthors,
     authors, maintainers, licensors,
     google_analytics, buylink,
     stateid, doctype)
  SELECT
    uuid, :next_major_version, :next_minor_version, CURRENT_TIMESTAMP,
    portal_type, moduleid,
    name, created, language,
    submitter, submitlog,
    abstractid, licenseid, parent, parentauthors,
    authors, maintainers, licensors,
    google_analytics, buylink,
    stateid, doctype
  FROM modules AS m JOIN previous AS p ON (m.module_ident = p.module_ident)
  RETURNING
    ident_hash(uuid, major_version, minor_version) AS ident_hash,
    module_ident),
keywords AS (
  INSERT INTO modulekeywords (module_ident, keywordid)
  SELECT i.module_ident, keywordid
  FROM modulekeywords AS mk, inserted AS i, previous AS p
  WHERE mk.module_ident = p.module_ident),
tags AS (
  INSERT INTO moduletags (module_ident, tagid)
  SELECT i.module_ident, tagid
  FROM moduletags AS mt, inserted AS i, previous AS p
  WHERE mt.module_ident = p.module_ident)
SELECT uuid, major_version, minor_version FROM inserted
"""


def republish_collection(trans, uuid, version):
    """Republish a collection's metadata.

    :param trans: the database transaction
    :param uuid: uuid of the content
    :param version: version to republish from
    :type version: tuple(int, int)
    :returns: the published version as a version tuple
              containing major and minor version.
    :rtypes: tuple(int, int)

    """
    (major_version, minor_version) = version
    bumped_version = bump_version(trans, uuid, is_minor_bump=True)

    stmt = text(_republish_tmplt).bindparams(
        uuid=uuid,
        major_version=major_version,
        minor_version=minor_version,
        next_major_version=bumped_version[0],
        next_minor_version=bumped_version[0],
    )
    result = trans.execute(stmt)
    uuid, major_version, minor_version = result.fetchone()
    return uuid, (major_version, minor_version)
