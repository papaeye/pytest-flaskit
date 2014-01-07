import pytest

from myapp import create_app


@pytest.fixture
def _app():
    return create_app()
