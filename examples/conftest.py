import pytest

from myapp import create_app


@pytest.fixture
def app():
    return create_app()
