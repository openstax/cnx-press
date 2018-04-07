from sqlalchemy.sql import text

from press.publishing.republish import republish_collection


_uuids_for_moduleid_query = text("""
SELECT uuid, ARRAY[major_version, minor_version]
FROM latest_modules
WHERE moduleid = any(:moduleids)
""")

_collection_includes_query = text("""
WITH RECURSIVE t(nodeid, parent_id, documentid, path) AS (
  SELECT tr.nodeid, tr.parent_id, tr.documentid, ARRAY[tr.nodeid]
  FROM trees tr
    WHERE tr.documentid = any(
      SELECT module_ident FROM modules WHERE moduleid = any(:moduleids))
UNION ALL
  SELECT c.nodeid, c.parent_id, c.documentid, path || ARRAY[c.nodeid]
  FROM trees c JOIN t ON (c.nodeid = t.parent_id)
  WHERE not c.nodeid = ANY(t.path)
)
SELECT DISTINCT m.uuid, ARRAY[m.major_version, m.minor_version]
FROM t JOIN latest_modules m ON (t.documentid = m.module_ident)
WHERE t.parent_id IS NULL AND moduleid != :collection_id;
""")

_legacy_identifiers_query = text("""
SELECT moduleid, version
FROM modules
WHERE ident_hash(uuid, major_version, minor_version) = any(:identifiers)
""")


def republish_books(collection, models, submission, registry):
    """Republish any Books containing the associated Pages (aka Modules).

    :param models: module list
    :type models: list of :class:`litezip.Module`
    :param submission: a two value tuple containing a userid
                       and submit message
    :type submission: tuple
    :param registry: the pyramid component architecture registry
    :type registry: :class:`pyramid.registry.Registry`

    :returns: a list containing an id and version within a tuple
              and database ident
    :rtype: list

    """
    engine = registry.engines['common']
    moduleids = [m.id for m in models]

    with engine.begin() as trans:
        # A mapping of uuid to version for newly published content
        changes = trans.execute(_uuids_for_moduleid_query,
                                moduleids=moduleids)
        change_map = {uuid: version for uuid, version in changes}

        # Gather a list of collections that contain the given modules
        collections = trans.execute(_collection_includes_query,
                                    moduleids=moduleids,
                                    collection_id=collection.id)

        # A list of republished collections
        republished = []  # [(uuid, (major_version, minor_version),), ...]
        # Republish the Collections
        for uuid, version in collections:
            uuid, new_version = republish_collection(trans, uuid, version,
                                                     change_map)
            republished.append((uuid, new_version))

        # Translate (uuid, version) to (moduleid, legacy-version)
        identifiers = ['@'.join([uuid, '.'.join([str(x) for x in version])])
                       for uuid, version in republished]
        result = trans.execute(_legacy_identifiers_query,
                               identifiers=identifiers)
        republished = [(moduleid, version)
                       for moduleid, version in result]
    return republished
