def test_root(client):
    assert client.get("/").status_code == 200


def test_usage_empty_log_is_empty_dict(client):
    assert client.get("/usage").json() == {}
