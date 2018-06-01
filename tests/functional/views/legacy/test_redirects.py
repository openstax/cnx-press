

def test_redirect_to_latest(
        content_util, persist_util, webapp):
    # Insert initial collection and modules.
    collection, tree, modules = persist_util.insert_all(
        *content_util.gen_collection()
    )
    # Republish to bump the version
    collection = content_util.bump_version(collection)
    collection, tree, modules = persist_util.insert_all(
        collection,
        tree,
        modules,
    )
    # Republish again, but this time with a non-current state.
    collection = content_util.bump_version(collection)
    collection, tree, modules = persist_util.insert_all(
        collection,
        tree,
        modules,
        collection_state='errored',
    )

    url = '/api/collections/{}/latest'.format(collection.id)
    resp = webapp.get(url)

    expected_location = 'http://legacy.localhost/content/{}/1.2'.format(
        collection.id,
    )
    assert resp.location == expected_location


def test_redirect_to_head(
        content_util, persist_util, webapp):
    # Insert initial collection and modules.
    collection, tree, modules = persist_util.insert_all(
        *content_util.gen_collection()
    )
    # Republish to bump the version
    collection = content_util.bump_version(collection)
    collection, tree, modules = persist_util.insert_all(
        collection,
        tree,
        modules,
    )
    # Republish again, but this time with a non-current state.
    collection = content_util.bump_version(collection)
    collection, tree, modules = persist_util.insert_all(
        collection,
        tree,
        modules,
        collection_state='errored',
    )

    url = '/api/collections/{}/head'.format(collection.id)
    resp = webapp.get(url)

    expected_location = 'http://legacy.localhost/content/{}/1.3'.format(
        collection.id,
    )
    assert resp.location == expected_location


def test_redirect_to_latest_not_found(webapp):
    url = '/api/collections/col99999999/latest'
    webapp.get(url, status=404)  # status == 404 is the test


def test_redirect_to_head_not_found(webapp):
    url = '/api/collections/col99999999/head'
    webapp.get(url, status=404)  # status == 404 is the test


def test_redirect_for_version_not_found(webapp):
    url = '/api/collections/col99999999/1.2'
    webapp.get(url, status=404)  # status == 404 is the test
