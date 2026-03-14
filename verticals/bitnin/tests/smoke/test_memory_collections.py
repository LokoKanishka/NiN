from verticals.bitnin.services.bitnin_memory_indexer.collections import QdrantCollectionManager


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(self.status_code)


class FakeSession:
    def __init__(self):
        self.created = None

    def get(self, url, timeout=0):
        if url.endswith("/collections"):
            return FakeResponse(payload={"result": {"collections": []}})
        if url.endswith("/collections/bitnin_episodes"):
            if self.created:
                return FakeResponse(payload={"result": {"config": {"params": {"vectors": {"size": 768}}}}})
            return FakeResponse(status_code=404)
        raise AssertionError(url)

    def put(self, url, json=None, timeout=0):
        self.created = json
        return FakeResponse(payload={"status": "ok"})


def test_ensure_collection_creates_expected_vector_size():
    session = FakeSession()
    manager = QdrantCollectionManager(base_url="http://fake-qdrant", session=session)
    result = manager.ensure_collection(name="bitnin_episodes", vector_size=768)
    assert session.created["vectors"]["size"] == 768
    assert result["config"]["params"]["vectors"]["size"] == 768
