import collections
import functools

import pytest
from flask import message_flashed, template_rendered


__version__ = '0.1.dev1'


@pytest.fixture(autouse=True)
def _flask_app_wrapper(request):
    if 'app' not in request.fixturenames:
        return

    app = request.getfuncargvalue('app')
    ctx = app.app_context()
    ctx.push()
    request.addfinalizer(ctx.pop)


try:
    from alembic import command
    from alembic.config import Config
    from flask.ext.sqlalchemy import _SignallingSession as SignallingSession
    from sqlalchemy import MetaData, Table, engine_from_config, orm
except ImportError:
    pass
else:
    class _SignallingSession(SignallingSession):

        def __init__(self, db, **options):
            self.app = db.get_app()
            self._model_changes = {}
            options.setdefault('bind', db.engine)
            options.setdefault('binds', db.get_binds(self.app))
            orm.Session.__init__(self, **options)

    def _create_scoped_session(db, options=None):
        """Helper factory method that creates a scoped session."""
        if options is None:
            options = {}
        scopefunc = options.pop('scopefunc', None)
        return orm.scoped_session(
            orm.sessionmaker(class_=_SignallingSession, db=db, **options),
            scopefunc=scopefunc)

    @pytest.fixture(scope='session')
    def engine(request, alembic_config):
        engine = engine_from_config(alembic_config)

        config = Config()
        for key, value in alembic_config.items():
            config.set_main_option(key, value)

        command.upgrade(config, 'head')

        def teardown():
            command.downgrade(config, 'base')
            Table('alembic_version', MetaData()).drop(bind=engine)
        request.addfinalizer(teardown)

        return engine

    @pytest.fixture(autouse=True)
    def _flask_db_wrapper(request):
        if 'db' not in request.fixturenames:
            return

        db = request.getfuncargvalue('db')
        engine = request.getfuncargvalue('engine')
        connection = engine.connect()
        transaction = connection.begin()

        options = dict({'bind': connection, 'binds': {}},
                       **getattr(db, 'session_options', {}))
        db.session = _create_scoped_session(db, options)

        def teardown():
            db.session.close()
            transaction.rollback()
            connection.close()
        request.addfinalizer(teardown)


@pytest.yield_fixture
def client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture
def request_context(request, app):
    ctx = app.test_request_context()
    ctx.push()
    request.addfinalizer(ctx.pop)
    return ctx


@pytest.fixture
def templates(request, app):
    Record = collections.namedtuple('Record', 'template context')

    records = []

    def record(sender, template, context, **extra):
        records.append(Record(template, context))
    template_rendered.connect(record, app)

    def teardown():
        template_rendered.disconnect(record, app)
    request.addfinalizer(teardown)

    return records


@pytest.fixture
def flashes(request, app):
    Record = collections.namedtuple('Record', 'message category')

    records = []

    def record(sender, message, category, **extra):
        records.append(Record(message, category))
    message_flashed.connect(record, app)

    def teardown():
        message_flashed.disconnect(record, app)
    request.addfinalizer(teardown)

    return records


def pytest_configure(config):
    config.addinivalue_line('markers',
                            'request_with_xhr: mark tests to request '
                            'adding X-Requested-With header.')
    config.addinivalue_line('markers',
                            'request_with_csrf_token: mark tests to request '
                            'adding dummy csrf token to header.')


@pytest.fixture(autouse=True)
def _request_with_xhr_marker(request):
    marker = request.keywords.get('request_with_xhr')
    if marker is not None:
        client = request.getfuncargvalue('client')
        client.open = request_with_xhr(client.open)


def request_with_xhr(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        kwargs.setdefault('headers', [])
        kwargs['headers'].append(('X-Requested-With', 'XMLHttpRequest'))
        return f(*args, **kwargs)
    return wrapper


@pytest.fixture(autouse=True)
def _request_with_csrf_token_marker(request):
    marker = request.keywords.get('request_with_csrf_token')
    if marker is None:
        return

    app = request.getfuncargvalue('app')
    # Flask-SeaSurf's defaults
    cookie_name = app.config.get('CSRF_COOKIE_NAME', '_csrf_token')
    header_name = app.config.get('CSRF_HEADER_NAME', 'X-CSRFToken')

    csrf_token = 'dummy csrf token'

    client = request.getfuncargvalue('client')
    with client.session_transaction() as session:
        session[cookie_name] = csrf_token

    wrapper = request_with_csrf_token(header_name, csrf_token)
    client.open = wrapper(client.open)


def request_with_csrf_token(header_name, csrf_token):
    def wrapper(f):
        @functools.wraps(f)
        def _wrapper(*args, **kwargs):
            kwargs.setdefault('headers', [])
            kwargs['headers'].append((header_name, csrf_token))
            return f(*args, **kwargs)
        return _wrapper
    return wrapper
