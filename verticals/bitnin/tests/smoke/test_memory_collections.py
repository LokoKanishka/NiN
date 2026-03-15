import json
import urllib.request
import urllib.error
from unittest.mock import MagicMock, patch
from verticals.bitnin.services.bitnin_memory_indexer.collections import QdrantCollectionManager

def test_ensure_collection_creates_expected_vector_size():
    with patch("urllib.request.urlopen") as mock_url:
        # Mock for get_collection (404) then put (200) then get_collection (200)
        mock_res_404 = MagicMock()
        mock_res_404.getcode.return_value = 404
        mock_res_404.__enter__.return_value = mock_res_404
        mock_res_404.read.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
        # Actually, for get_collection, it handles 404 naturally in _request
        
        # Scenario: get_collection -> 404 (None) -> PUT -> 200 -> get_collection -> 200
        
        # 1. GET /collections/bitnin_episodes -> 404
        response_404 = MagicMock()
        response_404.__enter__.side_effect = urllib.error.HTTPError("http://fake-qdrant/collections/bitnin_episodes", 404, "Not Found", {}, None)
        
        # 2. PUT /collections/bitnin_episodes -> 200
        response_put = MagicMock()
        response_put.__enter__.return_value = response_put
        response_put.read.return_value = json.dumps({"result": "ok"}).encode("utf-8")
        
        # 3. GET /collections/bitnin_episodes -> 200
        response_get_ok = MagicMock()
        response_get_ok.__enter__.return_value = response_get_ok
        response_get_ok.read.return_value = json.dumps({
            "result": {
                "config": {"params": {"vectors": {"size": 768}}}
            }
        }).encode("utf-8")
        
        mock_url.side_effect = [response_404, response_put, response_get_ok]
        
        manager = QdrantCollectionManager(base_url="http://fake-qdrant")
        result = manager.ensure_collection(name="bitnin_episodes", vector_size=768)
        assert result["config"]["params"]["vectors"]["size"] == 768
