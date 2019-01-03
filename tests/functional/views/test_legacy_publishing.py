from lxml import etree

from litezip.main import COLLECTION_NSMAP


a_username = 'user1'
a_passwd = 'foobar'


def test_publishing_invalid_zip(tmpdir, webapp):
    webapp.authorization = ('Basic', (a_username, a_passwd))

    file = tmpdir.mkdir('test').join('foo.txt')
    file.write('foo bar')

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
        expect_errors=True,
    )
    assert resp.status_code == 400
    expected_msgs = [
        {'id': 1,
         'message': 'The given file is not a valid zip formatted file.'},
    ]
    assert resp.json['messages'] == expected_msgs


def test_publishing_noauth_zip(tmpdir, webapp):

    file = tmpdir.mkdir('test').join('foo.txt')
    file.write('foo bar')

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
        expect_errors=True,
    )
    assert resp.status_code == 401
    expected_msgs = [
        {'id': 5,
         'message': 'Unauthorized',
         'error': 'Nothing to see here.'}
    ]
    assert resp.json['messages'] == expected_msgs


def test_publishing_invalid_revision_litezip(content_util, persist_util,
                                             webapp, db_engines, db_tables):
    webapp.authorization = ('Basic', (a_username, a_passwd))

    # Insert initial collection and modules.
    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)

    # Insert a new module ...
    new_module = content_util.gen_module(relative_to=collection)
    new_module = persist_util.insert_module(new_module)
    # ... remove second element from the tree ...
    tree.pop(1)
    # ... and append the new module to the tree.
    tree.append(content_util.make_tree_node_from(new_module))
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    struct = tuple([collection, new_module])

    # Modify the collection content to make it invalid.
    with collection.file.open('rb') as fb:
        xml = etree.parse(fb)
        elm = xml.xpath('//col:metadata', namespaces=COLLECTION_NSMAP)[0]
        # Add an invalid element.
        elm.insert(
            0,
            etree.Element(
                '{{{}}}wordlist'.format(COLLECTION_NSMAP['md']),
                nsmap=COLLECTION_NSMAP))
    with collection.file.open('wb') as fb:
        # Write the modified xml back to file.
        fb.write(etree.tounicode(xml).encode('utf8'))
    # Modify the module content to make it invalid.
    with new_module.file.open('rb') as fb:
        xml = etree.parse(fb)
        query = xml.xpath('//md:keywordlist', namespaces=COLLECTION_NSMAP)
        if query:
            elm = query[0]
            elm.getparent().remove(elm)
        elm = xml.xpath('//c:metadata', namespaces=COLLECTION_NSMAP)[0]
        # Add a valid element, but with empty (invalid) contents.
        elm.insert(
            0,
            etree.Element(
                '{{{}}}keywordlist'.format(COLLECTION_NSMAP['md']),
                nsmap=COLLECTION_NSMAP))
        # Add an invalid element.
        elm.insert(
            0,
            etree.Element(
                '{{{}}}wordlist'.format(COLLECTION_NSMAP['md']),
                nsmap=COLLECTION_NSMAP))
    with new_module.file.open('wb') as fb:
        # Write the modified xml back to file.
        fb.write(etree.tounicode(xml).encode('utf8'))

    # Compress to zip file as payload
    file = content_util.mk_zipfile_from_litezip_struct(struct)

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
        expect_errors=True,
    )
    assert resp.status_code == 400
    expected_msgs = [
        {'id': 2,
         'message': 'validation issue',
         'item': 'collection.xml',
         'error': ('3:319 -- error: element "md:wordlist" not allowed'
                   ' anywhere; expected element "md:abstract", "md:actors",'
                   ' "md:ancillary", "md:content-id", "md:content-url",'
                   ' "md:course-code", "md:created", "md:derived-from",'
                   ' "md:education-levellist", "md:extended-attribution",'
                   ' "md:homepage", "md:institution", "md:instructor",'
                   ' "md:keywordlist", "md:language", "md:license",'
                   ' "md:objectives", "md:repository", "md:revised",'
                   ' "md:roles", "md:short-title", "md:subjectlist",'
                   ' "md:subtitle", "md:title", "md:version" or'
                   ' "md:version-history"'),
         },
        {'id': 2,
         'message': 'validation issue',
         'item': '{}/index.cnxml'.format(new_module.id),
         'error': ('5:460 -- error: element "md:wordlist" not allowed'
                   ' anywhere; expected element "md:abstract", "md:actors",'
                   ' "md:content-id", "md:content-url", "md:course-code",'
                   ' "md:created", "md:derived-from",'
                   ' "md:education-levellist", "md:extended-attribution",'
                   ' "md:homepage", "md:institution", "md:instructor",'
                   ' "md:keywordlist", "md:language", "md:license",'
                   ' "md:objectives", "md:repository", "md:revised",'
                   ' "md:roles", "md:short-title", "md:subjectlist",'
                   ' "md:subtitle", "md:title" or "md:version"'),
         },
        {'id': 2,
         'message': 'validation issue',
         'item': '{}/index.cnxml'.format(new_module.id),
         'error': ('5:920 -- error: element "md:keywordlist" incomplete;'
                   ' missing required element "md:keyword"'),
         },
    ]
    assert resp.json['messages'] == expected_msgs


def test_publishing_revision_litezip(
        content_util, persist_util, webapp, db_engines, db_tables):
    webapp.authorization = ('Basic', (a_username, a_passwd))

    # Insert initial collection and modules.

    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)

    # Insert a new module ...
    new_module = content_util.gen_module(relative_to=collection)
    new_module = persist_util.insert_module(new_module)
    # ... remove second element from the tree ...
    tree.pop(1)
    # ... and append the new module to the tree.
    tree.append(content_util.make_tree_node_from(new_module))

    # Change the module text, to make it publishable.
    index_cnxml = new_module.file.read_text()
    start_offset = index_cnxml.find('test document')
    new_module.file.write_text(index_cnxml[:start_offset] +
                               'TEST DOCUMENT' +
                               index_cnxml[start_offset + 13:])

    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    struct = tuple([collection, new_module])

    file = content_util.mk_zipfile_from_litezip_struct(struct)

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
        expect_errors=True,
    )
    assert resp.status_code == 200

    # Check resulting data. (id mapping and urls)
    t = db_tables
    id_mapping = {x['source_id']: x for x in resp.json}
    for model in struct:
        assert model.id in id_mapping
        publication_record = id_mapping[model.id]
        assert publication_record['id'] == model.id
        version = '1.2'
        assert publication_record['legacy_version'] == version
        url = publication_record['url']
        # FIXME We should visit this URL rather than check its parts.
        assert '/content/{}/{}'.format(model.id, version) in url

        # FIXME This functional test should not be directly communicating
        #       with the database. Instead it should be using other http
        #       routes to verify the contents.
        # Check the content is actually in the database
        #   and that the correct publisher and message was attributed.
        # Checking for content details is out-of-scope for this test.
        stmt = (
            t.modules.select()
            .where(t.modules.c.moduleid == model.id)
            .order_by(t.modules.c.major_version.desc(),
                      t.modules.c.minor_version.desc())
            .limit(1))
        result = db_engines['common'].execute(stmt).fetchone()
        assert result.version == version
        assert result.submitter == publisher
        assert result.submitlog == message


def test_publishing_overwrite_module_litezip(
        content_util, persist_util, webapp, db_engines, db_tables):
    webapp.authorization = ('Basic', (a_username, a_passwd))

    # Insert initial collection and modules.
    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)

    # Insert a new module ...
    new_module = content_util.gen_module(relative_to=collection)
    new_module = persist_util.insert_module(new_module)

    # ... remove second element from the tree ...
    tree.pop(1)
    # ... and append the new module to the tree.
    tree.append(content_util.make_tree_node_from(new_module))
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)

    struct = tuple([collection, new_module])

    file = content_util.mk_zipfile_from_litezip_struct(struct)

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication (version becomes 1.2)
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
        expect_errors=True,
    )
    assert 200 == resp.status_code

    # Try to submit the publication again (version 1.1)
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
        expect_errors=True,
    )
    assert 400 == resp.status_code
    expected_msgs = [
        {
            "id": 3,
            "message": "stale version",
            "item": collection.id,
            "error": "checked out version is 1.1"
                     " but currently published is 1.2"
        }
    ]
    assert expected_msgs == resp.json['messages']


def test_publishing_overwrite_collection_litezip(
        content_util, persist_util, webapp, db_engines, db_tables):
    webapp.authorization = ('Basic', (a_username, a_passwd))

    # Insert initial collection and modules.
    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)

    # ... remove second element from the tree ...
    tree.pop(1)
    new_modules = [module for (i, module) in enumerate(modules) if i != 1]

    struct = tuple([collection, new_modules[0], ])

    file = content_util.mk_zipfile_from_litezip_struct(struct)

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
        expect_errors=False,
    )
    assert 202 == resp.status_code

    # Submit a publication, again.
    # Note that this increases the version to 1.2
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
        expect_errors=True,
    )
    assert 202 == resp.status_code


def test_publishing_no_changes(
        content_util, persist_util, webapp, db_engines, db_tables):
    webapp.authorization = ('Basic', (a_username, a_passwd))

    # Insert initial collection and modules.
    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)

    struct = tuple([collection, ])

    file = content_util.mk_zipfile_from_litezip_struct(struct)

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
    )

    assert resp.status_code == 202


def test_publishing_unauthenticated(content_util, persist_util,
                                    webapp, db_engines, db_tables):
    # TODO: Test that publishing returns 401 for unathenticated requests
    #       and a proper `messages` json response along with it.

    # (Below this line is duplicate code from test_publishing_no_changes.)

    # Insert initial collection and modules.
    collection, tree, modules = content_util.gen_collection()
    modules = list([persist_util.insert_module(m) for m in modules])
    collection, tree, modules = content_util.rebuild_collection(collection,
                                                                tree)
    collection = persist_util.insert_collection(collection)

    struct = tuple([collection, ])

    file = content_util.mk_zipfile_from_litezip_struct(struct)

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post(
        '/api/publish-litezip',
        form_data,
        upload_files=file_data,
        expect_errors=True,
    )
    assert resp.status_code == 401
    expected_msgs = [
        {
            "id": 5,
            "message": "Unauthorized",
            "error": "Nothing to see here."
        }
    ]
    assert resp.json['messages'] == expected_msgs
