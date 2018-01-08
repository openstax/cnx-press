import os
import pathlib
import random
import shutil
import tempfile

import jinja2
import pytest
from litezip import Module
from litezip.main import COLLECTION_NSMAP
from lxml import etree
from pyramid.settings import asbool
from sqlalchemy.sql import text


TEMPLATE_DIR = pathlib.Path(__file__).parent / '_templates'
with (TEMPLATE_DIR / 'module.xml').open('r') as fb:
    MODULE_DOC = fb.read()


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


PERSONS = (
    # personid, firstname, surname, fullname, email
    ['user1', 'User', 'One', 'User One', 'user1@example.com'],
    ['user2', 'User', 'Two', 'User Duo', 'user2@example.com'],
    ['user3', 'User', 'Three', 'Usuario Tres', 'user3@example.com'],
    ['user4', 'User', 'Four', 'User IIII', 'user4@example.com'],
)


SUBJECTS = (
    'Arts',
    'Business',
    'Humanities',
    'Mathematics and Statistics',
    'Science and Technology',
    'Social Sciences',
)


@pytest.fixture(scope='session')
def db_tables_session_scope(db_engines):
    from cnxdb.contrib.pytest import db_tables
    return db_tables(db_engines)


@pytest.fixture
def db_tables(db_tables_session_scope):
    # override cnx-db's db_tables to use the session scoped version.
    return db_tables_session_scope


@pytest.fixture(scope='session', autouse=True)
def testing(db_engines, db_tables_session_scope):
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
    column_names = ['personid', 'firstname', 'surname', 'fullname', 'email']
    db_engines['common'].execute(
        t.persons.insert(),
        [dict(zip(column_names, x)) for x in PERSONS])


class _ContentUtil:

    _word_catalog_filepath = '/usr/share/dict/words'
    _persons = PERSONS
    _subjects = SUBJECTS

    def __init__(self):
        with open(self._word_catalog_filepath, 'r') as fb:
            word_catalog = list([x for x in fb.read().splitlines()
                                 if len(x) >= 3 and "'" not in x])
        self.word_catalog = word_catalog
        self._created_dirs = []

    def _clean_up(self):
        for dir in self._created_dirs:
            shutil.rmtree(str(dir))

    def _mkdir(self):
        dir = pathlib.Path(tempfile.mkdtemp())
        self._created_dirs.append(dir)
        return dir

    def _rand_id_num(self):
        return random.randint(10000, 99999)

    def randid(self, prefix='m'):
        return '{}{}'.format(prefix, self._rand_id_num())

    def randword(self):
        return random.choice(self.word_catalog)

    def randperson(self):
        return random.choice(self._persons)

    def randsubj(self):
        return random.choice(self._subjects)

    def rand_module_id(self):
        return 'm{}'.format(self._rand_id_num)

    def gen_module_metadata(self, id=None):
        return {
            'id': id,
            'version': '1.1',
            'created': '2010/12/15 10:58:00 -0600',
            'revised': '2011/08/16 13:55:25 -0500',
            'title': ' '.join([self.randword(),
                               self.randword(),
                               self.randword()]),
            'license_url': 'http://creativecommons.org/licenses/by-nc-sa/4.0/',
            'language': 'en',
            'authors': set([self.randperson()[0],
                            self.randperson()[0]]),
            'maintainers': set([self.randperson()[0],
                                self.randperson()[0]]),
            'licensors': [self.randperson()[0]],
            'keywords': [self.randword()
                         for x in range(1, random.randint(1, 5))],
            'subjects': [self.randsubj()],
            'abstract': 'testing abstract',
        }

    def gen_cnxml(self, metadata, resources, terms=[]):
        template = jinja2.Template(MODULE_DOC)
        return template.render(metadata=metadata, resources=resources,
                               terms=' '.join(terms))

    def gen_module(self, resources=[]):
        id = None
        module_dir = self._mkdir()
        module_filepath = module_dir / 'm_____.cnxml'
        metadata = self.gen_module_metadata(id=id)
        with module_filepath.open('w') as fb:
            fb.write(self.gen_cnxml(metadata, resources))
        return Module(id, pathlib.Path(module_filepath), resources)


@pytest.fixture(scope='session')
def content_util(request):
    util = _ContentUtil()
    request.addfinalizer(util._clean_up)
    return util


class _PersistUtil:

    def __init__(self, db_engines, db_tables, content_util):
        self.db_engines = db_engines
        self.db_tables = db_tables
        self.content_util = content_util

    def insert_module(self, model):
        # This is validly used here because the tests associated with
        # this parser functions are outside the scope of persistent
        # actions dealing with the database.
        from press.parsers import parse_module_metadata
        metadata = parse_module_metadata(model)

        engine = self.db_engines['common']
        t = self.db_tables

        if metadata.id is None:
            moduleid = self.content_util.randid()
        else:
            moduleid = metadata.id

        with engine.begin() as trans:
            # Insert module metadata
            result = trans.execute(t.abstracts.insert()
                                   .values(abstract=metadata.abstract))
            abstractid = result.inserted_primary_key[0]
            result = trans.execute(
                t.licenses.select()
                .where(t.licenses.c.url == metadata.license_url))
            licenseid = result.fetchone().licenseid
            result = trans.execute(t.modules.insert().values(
                moduleid=moduleid,
                version=metadata.version,
                portal_type='Module',
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
                parent=None,
                parentauthors=None,
            ).returning(t.modules.c.module_ident, t.modules.c.moduleid))
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

            # Rewrite the content with the id
            with model.file.open('rb') as fb:
                xml = etree.parse(fb)
            elm = xml.xpath('//md:content-id', namespaces=COLLECTION_NSMAP)[0]
            elm.text = id
            with model.file.open('wb') as fb:
                fb.write(etree.tostring(xml))

            # Insert module files (content and resources)
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
            # TODO Insert resource files (images, pdfs, etc.)

        return Module(id, model.file, model.resources)


@pytest.fixture(scope='session')
def persist_util(request, db_engines, db_tables_session_scope, content_util):
    util = _PersistUtil(db_engines, db_tables_session_scope, content_util)
    return util
