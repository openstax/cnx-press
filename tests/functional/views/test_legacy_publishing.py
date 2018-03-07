from lxml import etree

from litezip.main import COLLECTION_NSMAP


def test_publishing_invalid_zip(tmpdir, webapp):
    file = tmpdir.mkdir('test').join('foo.txt')
    file.write('foo bar')

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post('/api/v3/publish', form_data, upload_files=file_data,
                       expect_errors=True)
    assert resp.status_code == 400
    expected_msgs = [
        {'id': 1,
         'message': 'The given file is not a valid zip formatted file.'},
    ]
    assert resp.json['messages'] == expected_msgs


def test_publishing_invalid_revision_litezip(
        content_util, persist_util, webapp, db_engines, db_tables):
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
        fb.write(etree.tostring(xml))
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
        fb.write(etree.tostring(xml))

    # Compress to zip file as payload
    file = content_util.mk_zipfile_from_litezip_struct(struct)

    publisher = 'user1'
    message = 'test http publish'

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post('/api/v3/publish', form_data, upload_files=file_data,
                       expect_errors=True)
    assert resp.status_code == 400
    expected_msgs = [
        {'id': 2,
         'message': 'validation issue',
         'item': 'collection.xml',
         'error': ('3:319 -- error: unknown element "wordlist" from '
                   'namespace "http://cnx.rice.edu/mdml"'),
         },
        {'id': 2,
         'message': 'validation issue',
         'item': '{}/index.cnxml'.format(new_module.id),
         'error': ('5:460 -- error: unknown element "wordlist" '
                   'from namespace "http://cnx.rice.edu/mdml"'),
         },
        {'id': 2,
         'message': 'validation issue',
         'item': '{}/index.cnxml'.format(new_module.id),
         'error': '5:920 -- error: unfinished element',
         },
    ]
    assert resp.json['messages'] == expected_msgs


def test_publishing_revision_litezip(
        content_util, persist_util, webapp, db_engines, db_tables):
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

    # Submit a publication
    with file.open('rb') as fb:
        file_data = [('file', 'contents.zip', fb.read(),)]
    form_data = {'publisher': publisher, 'message': message}
    resp = webapp.post('/api/v3/publish', form_data, upload_files=file_data)
    assert resp.status_code == 200

    # Check resulting data. (id mapping and urls)
    id_mapping = {x['source_id']: x for x in resp.json}
    for model in struct:
        assert model.id in id_mapping
        publication_record = id_mapping[model.id]
        assert publication_record['id'] == model.id
        assert publication_record['version'] == '1.2'
        url = publication_record['url']
        # FIXME We should visit this URL rather than check it's parts.
        assert '/content/{}/{}'.format(model.id, '1.2') in url

    # FIXME This functional test should not be directly communicating
    #       with the database. Instead it should be using other http
    #       routes to verify the contents.
    # Check the content is actually in the database
    #   and that the correct publisher and message was attributed.
    # Checking for content details is out-of-scope for this test.
    t = db_tables
    for model in struct:
        stmt = (
            t.modules.select()
            .where(t.modules.c.moduleid == model.id)
            .order_by(t.modules.c.major_version.desc())
            .limit(1))
        result = db_engines['common'].execute(stmt).fetchone()
        assert result.version == '1.2'
        assert result.submitter == publisher
        assert result.submitlog == message
