from uuid import UUID

from sqlalchemy.sql import text

from .helpers import bump_version


__all__ = (
    'republish_collection',
)


_republish_collection = text("""\
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
    uuid, major_version, minor_version, module_ident
),
keywords AS (
  INSERT INTO modulekeywords (module_ident, keywordid)
  SELECT i.module_ident, keywordid
  FROM modulekeywords AS mk, inserted AS i, previous AS p
  WHERE mk.module_ident = p.module_ident
),
tags AS (
  INSERT INTO moduletags (module_ident, tagid)
  SELECT i.module_ident, tagid
  FROM moduletags AS mt, inserted AS i, previous AS p
  WHERE mt.module_ident = p.module_ident
)
SELECT uuid, major_version, minor_version FROM inserted
""")


_collection_tree_sql = text("""\
WITH RECURSIVE t(nodeid, parent_id, documentid, title, childorder, latest,
                 uuid, major_version, minor_version, path) AS (
  SELECT
    tr.nodeid, tr.parent_id, tr.documentid,
    tr.title, tr.childorder, tr.latest,
    m.uuid, m.major_version, m.minor_version,
    ARRAY[tr.nodeid]
  FROM trees AS tr
    JOIN modules AS m ON (tr.documentid = m.module_ident)
  WHERE m.uuid = :uuid
    AND m.major_version = :major_version
    AND m.minor_version = :minor_version
    AND tr.is_collated = FALSE
UNION ALL
  SELECT
    c.nodeid, c.parent_id, c.documentid, c.title, c.childorder, c.latest,
    m.uuid, m.major_version, m.minor_version,
    path || ARRAY[c.nodeid]
  FROM trees AS c
    JOIN t ON (c.parent_id = t.nodeid)
    JOIN modules AS m ON (c.documentid = m.module_ident)
  WHERE not c.nodeid = ANY(t.path) AND c.is_collated = FALSE
)
SELECT row_to_json(row) FROM (SELECT * FROM t) AS row""")

_tree_insert_sql = text("""\
INSERT INTO trees
  (nodeid, parent_id,
   documentid,
   title, childorder, latest)
VALUES
  (DEFAULT, :parent_id,
   (SELECT module_ident
    FROM modules
    WHERE uuid = :uuid
      AND major_version = :major_version
      AND minor_version = :minor_version
    ),
   :title, :childorder, :latest)
RETURNING nodeid""")


def republish_collection(trans, uuid, version, change_map):
    """Republish a collection.

    :param trans: the database transaction
    :param uuid: uuid of the content
    :param version: version to republish from
    :type version: tuple(int, int)
    :param change_map: a mapping of uuids to versions for changed
                       content; the changed content is likely part of the
                       broader publication
    :type change_map: dict
    :returns: the published version as a version tuple
              containing major and minor version.
    :rtypes: tuple(int, int)

    """
    (major_version, minor_version) = version
    bumped_version = bump_version(trans, uuid, is_minor_bump=True)

    result = trans.execute(
        _republish_collection,
        uuid=uuid,
        major_version=major_version,
        minor_version=minor_version,
        next_major_version=bumped_version[0],
        next_minor_version=bumped_version[1],
    )
    uuid, new_major_version, new_minor_version = result.fetchone()

    # Add this new version to the change map
    change_map[uuid] = (new_major_version, new_minor_version)
    # Rebuild the collection tree from the previous version's tree
    _rebuild_collection_tree(trans, uuid, version, change_map)

    return uuid, (new_major_version, new_minor_version)


def _rebuild_collection_tree(trans, uuid, version, change_map):
    """

    Rebuild the collection tree based on the previous version's tree
    but with references to the newly published modules.

    :param trans: the database transaction
    :param uuid: uuid of the content
    :param version: version to republish from
    :type version: tuple(int, int)
    :param change_map: a mapping of uuids to versions for changed
                       content; the changed content is likely part of the
                       broader publication
    :type change_map: dict

    """
    (major_version, minor_version) = version

    def get_tree():
        result = trans.execute(
            _collection_tree_sql,
            uuid=uuid,
            major_version=major_version,
            minor_version=minor_version,
        )
        for row in result:
            yield row[0]

    def insert(fields):
        result = trans.execute(_tree_insert_sql, **fields)
        return result.fetchone()[0]

    tree = {}  # {<current-nodeid>: {<row-data>...}, ...}
    children = {}  # {<nodeid>: [<child-nodeid>, ...], <child-nodeid>: [...]}
    for node in get_tree():
        tree[node['nodeid']] = node
        children.setdefault(node['parent_id'], [])
        children[node['parent_id']].append(node['nodeid'])

    def build_tree(nodeid, parent_id=None):
        node = tree[nodeid]
        node['parent_id'] = parent_id
        node_uuid = UUID(node['uuid'])
        if change_map.get(node_uuid) is not None \
           and (node['latest'] or parent_id is None):
            node['major_version'] = change_map[node_uuid][0]
            node['minor_version'] = change_map[node_uuid][1]
        new_nodeid = insert(node)
        for child_nodeid in children.get(nodeid, []):
            build_tree(child_nodeid, new_nodeid)

    root_node = children[None][0]
    build_tree(root_node)
