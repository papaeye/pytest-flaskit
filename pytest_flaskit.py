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


@pytest.fixture(autouse=True)
def _flask_db_wrapper(request):
    if 'db' not in request.fixturenames:
        return

    db = request.getfuncargvalue('db')
    db.create_all()

    def teardown():
        db.session.remove()
        db.drop_all()
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
