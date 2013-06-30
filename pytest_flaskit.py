import collections

import pytest
from flask import message_flashed, template_rendered


__version__ = '0.1.dev1'


@pytest.fixture
def app(request, _app):
    ctx = _app.app_context()
    ctx.push()
    request.addfinalizer(ctx.pop)
    return _app


@pytest.fixture
def db(request, app, _db):
    _db.create_all()

    def teardown():
        _db.session.remove()
        _db.drop_all()
    request.addfinalizer(teardown)
    return _db


@pytest.fixture
def client(request, app):
    client = app.test_client()
    client.__enter__()

    def teardown():
        client.__exit__(None, None, None)
    request.addfinalizer(teardown)
    return client


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
