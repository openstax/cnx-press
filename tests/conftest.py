import hashlib
import os
import pathlib
import random
import shutil
import tempfile
import zipfile
from copy import copy, deepcopy

import jinja2
import pretend
import pytest
from cnxdb.init import init_db
from litezip import Collection, Module, Resource
from litezip.main import COLLECTION_NSMAP
from lxml import etree
from pyramid import testing as pyramid_testing
from pyramid.request import apply_request_extensions, Request
from pyramid.settings import asbool
from recordclass import recordclass
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.sql import select, text

from .helpers import element_tree_from_model


TEMPLATE_DIR = pathlib.Path(__file__).parent / '_templates'
with (TEMPLATE_DIR / 'module.xml').open('r') as fb:
    MODULE_DOC = fb.read()
with (TEMPLATE_DIR / 'collection.xml').open('r') as fb:
    COLLECTION_DOC = fb.read()


def _maybe_set(env_var, value):
    """Only set the env_var if it doesn't already contain a value."""
    os.environ.setdefault(env_var, value)
    return os.environ[env_var]


@pytest.fixture(scope='session')
def keep_shared_directory():
    """Returns a True | False when based on the value of
    the ``KEEP_SHARED_DIR`` environment variable. Default is False

    """
    # This fixture isn't for reuse, but it does mean that it's
    # documented as a fixture the end-user can see via the pytest UI.
    return asbool(os.environ.get('KEEP_SHARED_DIR', False))


@pytest.fixture(scope='session')
def env_vars(keep_shared_directory):
    """Set up the applications environment variables."""
    temp_shared_directory = tempfile.mkdtemp('shared')
    shared_directory = _maybe_set('SHARED_DIR', temp_shared_directory)

    yield os.environ

    # Set ``KEEP_SHARED_DIR=1`` to keep the tests "shared directory"
    # if the shared directory isn't the temp directory.
    if not keep_shared_directory \
       and shared_directory != temp_shared_directory:
        for f in pathlib.Path(shared_directory).glob('*'):
            if f.name == '.gitkeep':
                continue
            elif f.is_dir():
                shutil.rmtree(f)
            else:
                f.unlink()
    shutil.rmtree(temp_shared_directory)


# TODO move to functional/conftest.py when unit/* tests no longer depend on it
@pytest.fixture
def app(env_vars):
    # Deprecated in favor of either making your test use pretend.stub
    # or be a functional test using WebTest
    from press.config import configure
    config = configure()
    config.commit()

    # Create a real request object with no real destination or attribution
    request = Request({})

    # Initialize the configuration and globalize the app's ZCA registry
    config.begin(request=request)

    # Set the registry on the request (something done by the router)
    setattr(request, 'registry', config.registry)
    # Extend the request to include out custom request methods
    apply_request_extensions(request)

    yield config

    config.end()
    # For good measure call the pyramid's testing teardown
    pyramid_testing.tearDown()


PERSONS = (
    # personid, firstname, surname, fullname, email, passwd, groups
    ['user1', 'User', 'One', 'User One', 'user1@example.com',
        b'{SSHA}Tf5uQqRItW5v4j0WDM5w3cgIwfKKATpX', ['Maintainer']],
    ['user2', 'User', 'Two', 'User Duo', 'user2@example.com',
        b'{SSHA}Tf5uQqRItW5v4j0WDM5w3cgIwfKKATpX', ['Maintainer']],
    ['user3', 'User', 'Three', 'Usuario Tres', 'user3@example.com',
        b'{SSHA}Tf5uQqRItW5v4j0WDM5w3cgIwfKKATpX', ['Maintainer']],
    ['user4', 'User', 'Four', 'User IIII', 'user4@example.com',
        b'{SSHA}Tf5uQqRItW5v4j0WDM5w3cgIwfKKATpX', ['Maintainer']],
)


SUBJECTS = (
    'Arts',
    'Business',
    'Humanities',
    'Mathematics and Statistics',
    'Science and Technology',
    'Social Sciences',
)


# Hard coded here because there is not a method for inputting this value.
GOOGLE_ANALYTICS_CODE = 'abc123'


@pytest.fixture(scope='session')
def db_tables_session_scope(db_engines):
    from cnxdb.contrib.pytest import db_tables
    tables = db_tables(db_engines)
    return tables


@pytest.fixture
def db_tables(db_tables_session_scope):
    # override cnx-db's db_tables to use the session scoped version.
    return db_tables_session_scope


def _create_database(db_engines):
    url = copy(db_engines['super'].url)
    db_name = url.database
    common_user = db_engines['common'].url.username
    url.database = 'postgres'

    sys_engine = create_engine(url, isolation_level='AUTOCOMMIT')
    conn = sys_engine.connect()
    conn.execute(text('CREATE DATABASE "{}"'.format(db_name)))
    conn.execute(text('ALTER DATABASE "{}" OWNER TO {}'
                      .format(db_name, common_user)))
    conn.execute(text('GRANT ALL PRIVILEGES ON DATABASE "{}" TO {}'
                      .format(db_name, common_user)))
    sys_engine.dispose()


@pytest.fixture(scope='session')
def _init_database(db_engines):
    engine = db_engines['super']
    try:
        # Check for database
        engine.execute('select 1')
    except (ProgrammingError, OperationalError):
        # Create the database and initialize the schema
        _create_database(db_engines)
        init_db(db_engines['super'])
        # Assign priveleges to our common user.
        for element in ('tables', 'sequences',):
            engine.execute(
                text('GRANT ALL PRIVILEGES ON ALL {} '
                     'IN SCHEMA PUBLIC TO {}'
                     .format(element.upper(),
                             db_engines['common'].url.username)))
        engine.execute(
            text('REASSIGN OWNED BY {} TO {}'
                 .format(db_engines['super'].url.username,
                         db_engines['common'].url.username)))
    finally:
        # Dispose of any connection(s)
        engine.dispose()


@pytest.fixture(scope='session', autouse=True)
def testing(_init_database, db_engines, db_tables_session_scope):
    """This fixture clears all the tables prior to any test run.
    Additionally, it minimally sets up database content. This content
    is of the type that would not typically be handed by this application.

    """
    tables = (
        'trees',
        'modulecounts',
        'modulekeywords',
        'similarities',
        'modulefti',
        'module_files',
        'collated_fti',
        'moduletags',
        'moduleoptionalroles',
        'moduleratings',
        'document_baking_result_associations',
        'collated_file_associations',
        'modules',
        'latest_modules',
        'abstracts',
        'keywords',
        'files',
        'users',
        'overall_hit_ranks',
        'recent_hit_ranks',
        'persons',
        'print_style_recipes',
        'default_print_style_recipes',
        'document_hits',
        'service_state_messages',
        'publications',
        'role_acceptances',
        'license_acceptances',
        'document_acl',
        'pending_resource_associations',
        'pending_documents',
        'pending_resources',
        'api_keys',
        'document_controls',
    )
    # Clear out the tables
    t = db_tables_session_scope
    for table in tables:
        stmt = getattr(t, table).delete()
        db_engines['common'].execute(stmt)

    # Insert 'persons', because this application doesn't do people.
    # You either have a user before publishing or some other means of
    # creating a user exists.
    column_names = ['personid', 'firstname', 'surname', 'fullname', 'email',
                    'passwd', 'groups']
    db_engines['common'].execute(
        t.persons.insert(),
        [dict(zip(column_names, x)) for x in PERSONS])


@pytest.fixture
def pretend_logger():
    info = pretend.call_recorder(lambda *a, **kw: None)
    debug = pretend.call_recorder(lambda *a, **kw: None)
    exception = pretend.call_recorder(lambda *a, **kw: None)
    logger = pretend.stub(
        info=info,
        debug=debug,
        exception=exception,
    )
    return logger


# ###
#  Collection Tree models
# ###
SubCollection = recordclass('SubCollection',  # aka Tree Container
                            'title contents')
ModuleNode = recordclass('ModuleNode',  # aka Tree Node
                         'title id version version_at module')


# ###
#  Content Utility
# ###
class _ContentUtil:

    _word_catalog_filepath = '/usr/share/dict/words'
    _persons = PERSONS
    _subjects = SUBJECTS

    Module = Module
    Collection = Collection
    Resource = Resource

    def __init__(self):
        with open(self._word_catalog_filepath, 'r') as fb:
            word_catalog = list([x for x in fb.read().splitlines()
                                 if len(x) >= 3 and "'" not in x])
        self.word_catalog = word_catalog
        self._created_dirs = []
        # Import during singleton creation
        self.Resource = Resource

    def _clean_up(self):
        for dir in self._created_dirs[::-1]:
            shutil.rmtree(str(dir))

    def _mkdir(self, start_at=None):
        if start_at is None:
            dir = pathlib.Path(tempfile.mkdtemp())
        else:
            dirnames = tempfile._get_candidate_names()
            while True:
                dir = start_at / next(dirnames)
                try:
                    dir.mkdir()
                except FileExistsError:
                    continue
                break
        self._created_dirs.append(dir)
        return dir

    def _gen_dir(self, relative_to=None):
        dir = None
        if isinstance(relative_to, pathlib.Path):
            path = relative_to
            dir = path.is_file() and path.parent or path
        elif isinstance(relative_to, Module):
            dir = relative_to.file.parent.parent
        elif isinstance(relative_to, Collection):
            dir = relative_to.file.parent
        return self._mkdir(start_at=dir)

    def _rand_id_num(self):
        return random.randint(10000, 99999)

    def _parse_module_metadata(self, *args, **kwargs):
        # The parser is validly used here because it is unit tested
        # without using this utility.
        from press.parsers import parse_module_metadata
        return parse_module_metadata(*args, **kwargs)

    def _parse_collection_metadata(self, *args, **kwargs):
        # The parser is validly used here because it is unit tested
        # without using this utility.
        from press.parsers import parse_collection_metadata
        return parse_collection_metadata(*args, **kwargs)

    def randid(self, prefix='m'):
        return '{}{}'.format(prefix, self._rand_id_num())

    def randword(self):
        return random.choice(self.word_catalog)

    def randtitle(self):
        return ' '.join([self.randword(),
                         self.randword(),
                         self.randword()])

    def randperson(self):
        return random.choice(self._persons)

    def randsubj(self):
        return random.choice(self._subjects)

    def rand_module_id(self):
        return 'm{}'.format(self._rand_id_num)

    def copy_model(self, model, relative_to=None):
        """Copy the given model"""
        # This is mostly useful, because a copy of the object isn't enough
        # since much of the model's data is on the filesystem.

        model_type = type(model)
        new_model_dir = self._gen_dir(relative_to=relative_to)
        filename = {
            self.Collection: 'collection.xml',
            self.Module: 'index.cnxml',
        }[model_type]
        new_model_filepath = new_model_dir / filename

        # Copy content
        with new_model_filepath.open('w') as fb, model.file.open('r') as o:
            fb.write(o.read())
        # Copy resources
        new_resources = deepcopy(model.resources)

        return model_type(
            model.id,
            pathlib.Path(new_model_filepath),
            new_resources,
        )

    def gen_module_metadata(self, id=None, derived_from_metadata=None):
        return {
            'id': id,
            'version': '1.1',
            'created': '2010/12/15 10:58:00 -0600',
            'revised': '2011/08/16 13:55:25 -0500',
            'title': self.randtitle(),
            'license_url': 'http://creativecommons.org/licenses/by-nc-sa/4.0/',
            'language': 'en',
            'print_style': self.randword(),
            'authors': set([self.randperson()[0],
                            self.randperson()[0]]),
            'maintainers': set([self.randperson()[0],
                                self.randperson()[0]]),
            'licensors': [self.randperson()[0]],
            'keywords': [self.randword()
                         for x in range(1, random.randint(1, 5))],
            'subjects': [self.randsubj()],
            'abstract': self.randtitle(),
            'derived_from': derived_from_metadata,
        }

    def gen_cnxml(self, metadata, resources, terms=[]):
        template = jinja2.Template(MODULE_DOC)
        return template.render(metadata=metadata, resources=resources,
                               terms=' '.join(terms))

    def gen_colxml(self, metadata, tree):
        template = jinja2.Template(COLLECTION_DOC)
        return template.render(metadata=metadata, tree=tree)

    def gen_resource(self, data=None, filename=None,
                     media_type='text/plain', relative_to=None):
        if filename is None:
            filename = '_'.join([self.randword(), self.randword()]) + '.txt'

        resource_dir = self._gen_dir(relative_to=relative_to)
        resource_filepath = resource_dir / filename

        if data is not None:
            try:
                data.save(resource_filepath)
                data = resource_filepath.read_bytes()
            except AttributeError:  # Assume it's bytes
                resource_filepath.write_bytes(data)
        else:
            data = ' '.join([self.randtitle(),
                             self.randtitle()]).encode('utf-8')
            resource_filepath.write_bytes(data)

        sha1 = hashlib.sha1(data).hexdigest()

        return self.Resource(
            resource_filepath,
            filename,
            media_type,
            sha1,
        )

    def gen_module(self, id=None, resources=[], relative_to=None,
                   derived_from=None):
        id = not id and self.randid(prefix='m') or id
        module_dir = self._gen_dir(relative_to=relative_to)
        module_filepath = module_dir / 'index.cnxml'

        # Generate metadata
        if derived_from:
            derived_metadata = self._parse_collection_metadata(derived_from)
        else:
            derived_metadata = None
        metadata = self.gen_module_metadata(
            id=id,
            derived_from_metadata=derived_metadata,
        )

        with module_filepath.open('w') as fb:
            fb.write(self.gen_cnxml(metadata, resources))
        return self.Module(id, pathlib.Path(module_filepath), resources)

    def gen_collection(self, id=None, modules=[], resources=[],
                       relative_to=None, derived_from=None):
        id = not id and self.randid(prefix='col') or id
        relative_to = dir = self._gen_dir(relative_to=relative_to)
        filepath = dir / 'collection.xml'

        # Generate metadata
        if derived_from:
            derived_metadata = self._parse_collection_metadata(derived_from)
        else:
            derived_metadata = None
        metadata = self.gen_module_metadata(
            id=id,
            derived_from_metadata=derived_metadata,
        )

        # Generate the tree
        tree, modules = self.gen_collection_tree(
            modules=modules,
            relative_to=relative_to,
        )

        # Write the colxml to the filesystem
        with filepath.open('w') as fb:
            fb.write(self.gen_colxml(metadata, tree))
        collection = self.Collection(id, pathlib.Path(filepath), resources)

        return collection, tree, modules

    def gen_collection_tree(self, modules=[],
                            max_depth=1, depth=0, relative_to=None):
        """Returns a sequence containing a dict of title and contents
        and/or Module objects.

        """
        tree = []
        for module in modules:
            node = self.make_tree_node_from(module)
            tree.append(node)
        for x in range(2, 6):
            if random.randint(1, 40) % 2 == 0 or depth == max_depth:
                module = self.gen_module(relative_to=relative_to)
                modules.append(module)
                node = self.make_tree_node_from(module)
                tree.append(node)
            else:
                contents, additional_modules = self.gen_collection_tree(
                    max_depth=max_depth,
                    depth=depth + 1,
                    relative_to=relative_to)
                modules.extend(additional_modules)
                sub_col = SubCollection(title=self.randtitle(),
                                        contents=contents)
                tree.append(sub_col)
        return tree, modules

    def make_tree_node_from(self, module):
        metadata = self._parse_module_metadata(module)
        node = ModuleNode(id=metadata.id,
                          version='latest',
                          version_at=metadata.version,
                          title=metadata.title,
                          module=module)
        return node

    def _update_collection(self, collection, tree):
        metadata = self._parse_collection_metadata(collection)
        self._update_tree_contents(tree)
        with collection.file.open('w') as fb:
            fb.write(self.gen_colxml(metadata, tree))

    def _update_tree_contents(self, tree):
        for node in tree:
            if isinstance(node, SubCollection):
                self._update_tree_contents(node.contents)
            else:
                metadata = self._parse_module_metadata(node.module)
                node.title = metadata.title
                node.id = metadata.id
                node.version_at = metadata.version

    def _flatten_collection_tree_to_modules(self, tree):
        """Given a collection tree data structure,
        flatten this to a list of module nodes.

        """
        for node in tree:
            if isinstance(node, SubCollection):
                contents = node.contents
                yield from self._flatten_collection_tree_to_modules(contents)
            else:
                yield node.module

    def rebuild_collection(self, collection, tree):
        modules = list(self._flatten_collection_tree_to_modules(tree))
        self._update_collection(collection, tree)
        return collection, tree, modules

    def mk_zipfile_from_litezip_struct(self, struct):
        zip_file = self._mkdir() / 'contents.zip'
        base_dir = pathlib.Path(struct[0].id)
        with zipfile.ZipFile(str(zip_file), 'w') as zb:
            for model in struct:
                if isinstance(model, Collection):
                    file = model.file
                    rel_file_path = base_dir / model.file.name
                else:  # Module
                    file = model.file
                    # FIXME Workaround for the lack of actual m##### named
                    #       directories. This is because the 'new' content
                    #       story has not been implemented yet.
                    rel_file_path = base_dir / model.id / model.file.name
                zb.write(str(file), str(rel_file_path))
                # TODO Write resources into this zipfile
        return zip_file

    def bump_version(self, module):
        with element_tree_from_model(module) as xml:
            elm = xml.xpath('//md:version', namespaces=COLLECTION_NSMAP)[0]
            version = int(elm.text.split('.')[-1]) + 1
            elm.text = '1.{}'.format(version)
        return module

    def append_to_module(self, module, appendage=None):
        """Append the given ``appendage`` string to the given ``module``,
        then return the module object.

        """
        with element_tree_from_model(module) as xml:
            elm = xml.xpath('//c:content', namespaces=COLLECTION_NSMAP)[0]

            if appendage is None:
                appendage = 'fooppendage'
            elm_name = '{{{}}}para'.format(COLLECTION_NSMAP['c'])
            appendage_elm = etree.Element(
                elm_name,
                id=str(self._rand_id_num()),
            )
            appendage_elm.text = appendage
            elm.append(appendage_elm)
        return module

    def flatten_collection_tree_to_nodes(self, tree):
        """Given a collection tree, flatten it to end nodes (module items)."""
        for node in tree:
            if hasattr(node, 'contents'):
                yield from self.flatten_collection_tree_to_nodes(node.contents)
            else:
                yield node


@pytest.fixture(scope='session')
def content_util(request):
    util = _ContentUtil()
    request.addfinalizer(util._clean_up)
    return util


# ###
#  Persistence Utility
# ###
class _PersistUtil:

    def __init__(self, db_engines, db_tables, content_util):
        self.db_engines = db_engines
        self.db_tables = db_tables
        self.content_util = content_util

    def _insert_module_metadata(self, trans, metadata, type_,
                                _derived_from=None):
        """Insert the module metadata with using the given database
        transaction.

        ``_derived_from`` argument is for PersistUtil internal use only.
        Use the ``derive_from`` method to derive a copy.

        """
        t = self.db_tables

        result = trans.execute(t.abstracts.insert()
                               .values(abstract=metadata.abstract))
        abstractid = result.inserted_primary_key[0]
        result = trans.execute(
            t.licenses.select()
            .where(t.licenses.c.url == metadata.license_url))
        licenseid = result.fetchone().licenseid
        major_version = metadata.version.split('.')[-1]
        existing_metadata = trans.execute(
            t.modules.select().where(t.modules.c.moduleid == metadata.id)
        ).fetchone()
        # Assign values for existing metadata to be carried over
        if existing_metadata is not None:
            existing_uuid = existing_metadata.uuid
            parent_ident = existing_metadata.parent
            parent_authors = existing_metadata.parentauthors
        elif _derived_from is not None:  # Used during the derive action
            existing_uuid = None
            parent = trans.execute(
                t.modules.select()
                .where(t.modules.c.moduleid == _derived_from['id'])
                .where(t.modules.c.version == _derived_from['version'])
            ).fetchone()
            parent_ident = parent.module_ident
            parent_authors = parent.authors
        else:
            existing_uuid = None
            parent_ident = None
            parent_authors = None

        # Insert the core metadata
        result = trans.execute(
            t.modules.insert().values(
                uuid=existing_uuid,
                moduleid=metadata.id,
                major_version=major_version,
                portal_type=type_,
                name=metadata.title,
                created=metadata.created,
                revised=metadata.revised,
                abstractid=abstractid,
                licenseid=licenseid,
                doctype='',
                submitter='user1',
                submitlog='util inserted',
                language=metadata.language,
                authors=metadata.authors,
                maintainers=metadata.maintainers,
                licensors=metadata.licensors,
                parent=parent_ident,
                parentauthors=parent_authors,
                google_analytics=GOOGLE_ANALYTICS_CODE,
            ).returning(t.modules.c.module_ident, t.modules.c.moduleid)
        )
        ident, id = result.fetchone()

        # Insert subjects metadata
        stmt = (text('INSERT INTO moduletags '
                     'SELECT :module_ident AS module_ident, tagid '
                     'FROM tags WHERE tag = any(:subjects)')
                .bindparams(module_ident=ident,
                            subjects=list(metadata.subjects)))
        result = trans.execute(stmt)

        # Insert keywords metadata
        stmt = (text('INSERT INTO keywords (word) '
                     'SELECT iword AS word '
                     'FROM unnest(:keywords ::text[]) AS iword '
                     '     LEFT JOIN keywords AS kw ON (kw.word = iword) '
                     'WHERE kw.keywordid IS NULL')
                .bindparams(keywords=list(metadata.keywords)))
        trans.execute(stmt)
        stmt = (text('INSERT INTO modulekeywords '
                     'SELECT :module_ident AS module_ident, keywordid '
                     'FROM keywords WHERE word = any(:keywords)')
                .bindparams(module_ident=ident,
                            keywords=list(metadata.keywords)))
        trans.execute(stmt)
        return ident, id

    def _already_exists(self, trans, model, metadata):
        """Check if the given model already exists in the database.
        This is a simple check done by moduleid and version.
        It's assumed the programmer will not insert the same file twice.

        """
        t = self.db_tables
        stmt = (t.modules.select()
                .where(t.modules.c.moduleid == metadata.id)
                .where(t.modules.c.version == metadata.version))
        result = trans.execute(stmt)
        return bool(result.fetchone())

    def _set_state(self, trans, moduleid, version, state_name):
        stmt = (text('UPDATE modules '
                     'SET stateid = (SELECT stateid '
                     '               FROM modulestates '
                     '               WHERE statename = :state_name)'
                     'WHERE moduleid = :moduleid AND version = :version ')
                .bindparams(moduleid=moduleid, version=version,
                            state_name=state_name))
        trans.execute(stmt)

    def _insert_module_file(self, resource, module_ident):
        """Insert a resource file into the ``module_files`` table."""
        engine = self.db_engines['common']

        self.insert_resource(resource)

        stmt = text(
            "INSERT INTO module_files (module_ident, fileid, filename) "
            "VALUES ("
            "  :module_ident,"
            "  (SELECT fileid FROM files WHERE sha1 = :sha1),"
            "  :filename)"
        )
        engine.execute(
            stmt,
            module_ident=module_ident,
            sha1=resource.sha1,
            filename=resource.filename,
        )

    def insert_resource(self, resource):
        """Insert a resource file into the ``files`` table."""
        engine = self.db_engines['common']
        t = self.db_tables

        exists = engine.execute(
            select([t.files.c.fileid])
            .where(t.files.c.sha1 == resource.sha1)
        ).fetchone()

        if not exists:
            with resource.data.open('rb') as fp:
                engine.execute(
                    t.files.insert().values(
                        file=fp.read(),
                        sha1=resource.sha1,
                        media_type=resource.media_type,
                    )
                )

        return resource

    def derive_from(self, model):
        """Derive a copy of the given model. Insert this into the database
        with the changed title prefixed with "Derived copy of ".

        This returns a model for the newly inserted content.

        """
        model_cls_name = model.__class__.__name__
        type_name = model_cls_name.lower()
        id_prefix = {
            Module: 'm',
            Collection: 'col',
        }[type(model)]
        parse_metadata = getattr(
            self.content_util,
            '_parse_{}_metadata'.format(type_name),
        )
        md = parse_metadata(model)
        derived_from = {'id': md.id, 'version': md.version}
        insertion_method = getattr(self, 'insert_{}'.format(type_name))

        # Create a copy of the model
        derived_model = self.content_util.copy_model(model)

        # Change title, id, version, and derived-from
        with element_tree_from_model(derived_model) as xml:
            # Title
            elm = xml.xpath('//md:title', namespaces=COLLECTION_NSMAP)[0]
            elm.text = 'Derived copy of {}'.format(elm.text)
            # Id
            new_id = self.content_util.randid(prefix=id_prefix)
            elm = xml.xpath('//md:content-id', namespaces=COLLECTION_NSMAP)[0]
            elm.text = new_id
            # Version
            elm = xml.xpath('//md:version', namespaces=COLLECTION_NSMAP)[0]
            elm.text = '1.1'
            # Derived-from
            ns_prefix = {
                Module: 'c',
                Collection: 'col',
            }[type(model)]
            metadata_elm = xml.xpath(
                '//{}:metadata'.format(ns_prefix),
                namespaces=COLLECTION_NSMAP,
            )[0]
            derived_from_elm = etree.fromstring(
                '<derived-from xmlns="{}" url="{}"/>'
                .format(
                    COLLECTION_NSMAP['md'],
                    'http://cnx.org/content/{}/{}'.format(md.id, md.version),
                )
            )
            metadata_elm.append(derived_from_elm)

        # Recreate the model, because we changed the id
        derived_model = getattr(self.content_util, model_cls_name)(
            new_id,
            derived_model.file,
            derived_model.resources,
        )

        # Persist the model
        new_model = insertion_method(
            derived_model,
            _derived_from=derived_from,
        )

        # Return new model of derived copy
        return new_model

    def insert_module(self, model, _derived_from=None):
        # This is validly used here because the tests associated with
        # this parser functions are outside the scope of persistent
        # actions dealing with the database.
        from press.parsers import parse_module_metadata
        metadata = parse_module_metadata(model)

        engine = self.db_engines['common']
        t = self.db_tables

        # Anything inserted with this tool must already have a valid id
        assert metadata.id is not None

        with engine.begin() as trans:
            if self._already_exists(trans, model, metadata):
                return model

            # Insert module metadata
            ident, id = self._insert_module_metadata(
                trans,
                metadata,
                'Module',
                _derived_from=_derived_from,
            )

            # Rewrite the content with the id
            with model.file.open('rb') as fb:
                xml = etree.parse(fb)
            elm = xml.xpath('//md:content-id', namespaces=COLLECTION_NSMAP)[0]
            elm.text = id
            with model.file.open('wb') as fb:
                fb.write(etree.tounicode(xml).encode('utf8'))

            # Insert content files
            with model.file.open('rb') as fb:
                result = trans.execute(t.files.insert().values(
                    file=fb.read(),
                    media_type='text/xml',
                ))
            fileid = result.inserted_primary_key[0]
            result = trans.execute(t.module_files.insert().values(
                module_ident=ident,
                fileid=fileid,
                filename='index.cnxml',
            ))
        # Insert resource files (images, pdfs, etc.)
        for resource in model.resources:
            self._insert_module_file(resource, ident)

        return Module(id, model.file, model.resources)

    def insert_collection(self, model, _derived_from=None):
        # This is validly used here because the tests associated with
        # this parser functions are outside the scope of persistent
        # actions dealing with the database.
        from press.parsers import parse_collection_metadata
        metadata = parse_collection_metadata(model)

        engine = self.db_engines['common']
        t = self.db_tables

        # Anything inserted with this tool must already have a valid id
        assert metadata.id is not None

        with engine.begin() as trans:
            if self._already_exists(trans, model, metadata):
                return model

            # Insert metadata
            ident, id = self._insert_module_metadata(
                trans,
                metadata,
                'Collection',
                _derived_from=_derived_from,
            )

            # Rewrite the content with the id
            with model.file.open('rb') as fb:
                xml = etree.parse(fb)
            elm = xml.xpath('//md:content-id', namespaces=COLLECTION_NSMAP)[0]
            elm.text = id
            with model.file.open('wb') as fb:
                fb.write(etree.tounicode(xml).encode('utf8'))

            # Insert content files
            with model.file.open('rb') as fb:
                result = trans.execute(t.files.insert().values(
                    file=fb.read(),
                    media_type='text/xml',
                ))
            fileid = result.inserted_primary_key[0]
            result = trans.execute(t.module_files.insert().values(
                module_ident=ident,
                fileid=fileid,
                filename='collection.xml',
            ))
            self._set_state(trans, metadata.id, metadata.version, 'current')

        # Insert resource files (recipes, cover image, etc.)
        for resource in model.resources:
            self._insert_module_file(resource, ident)

        return Collection(id, model.file, model.resources)

    def insert_all(self, collection, tree, modules):
        """Persist all the modules and the collection.
        Returns the rebuilt collection, tree and modules.

        """
        modules = list([self.insert_module(m) for m in modules])
        collection, tree, modules = self.content_util.rebuild_collection(
            collection, tree)
        collection = self.insert_collection(collection)
        return collection, tree, modules


@pytest.fixture(scope='session')
def persist_util(request, db_engines, db_tables_session_scope, content_util):
    util = _PersistUtil(db_engines, db_tables_session_scope, content_util)
    return util
