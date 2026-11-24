def test_index_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'test title' in response.data
