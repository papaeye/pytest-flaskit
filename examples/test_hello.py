def test_hello(client):
    response = client.get('/')
    assert response.get_data() == b'Hello, world'
