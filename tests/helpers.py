
def compare_legacy_tree_similarity(db_tree, test_tree):
    """Compare the two types of tree, one coming from the database using
    `tree_to_json_for_legacy` and the other using the tree structure
    provided by the `content_util` testing utility.

    """
    for i, v in enumerate(db_tree):
        if v['id'].startswith('col'):
            assert test_tree[i].title == v['title']
            compare_legacy_tree_similarity(v['contents'],
                                           test_tree[i].contents)
        else:
            node = test_tree[i]
            assert v['id'] == node.id
            assert v['title'] == node.title
            assert v['version'] == node.version_at
