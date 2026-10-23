import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

from api import Handler, cache


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True
        )
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        cache.clear()

    def get_json(self, path):
        try:
            with urlopen(self.base_url + path, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_health_and_places(self):
        status, health = self.get_json("/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")

        status, places = self.get_json("/places")
        self.assertEqual(status, 200)
        self.assertIn("GATE", places["places"])
        self.assertIn("CAFE", places["places"])

    def test_shortest_route_and_cache(self):
        path = "/route?start=GATE&goal=CAFE"

        status, first = self.get_json(path)
        self.assertEqual(status, 200)
        self.assertTrue(first["reachable"])
        self.assertEqual(first["distance_m"], 200)
        self.assertFalse(first["cached"])
        self.assertTrue(first["directions"])

        status, second = self.get_json(path)
        self.assertEqual(status, 200)
        self.assertEqual(second["distance_m"], 200)
        self.assertTrue(second["cached"])

    def test_closed_road_changes_route(self):
        path = (
            "/route?start=GATE&goal=CAFE"
            "&closed_from=ADMIN&closed_to=CAFE"
        )

        status, route = self.get_json(path)
        self.assertEqual(status, 200)
        self.assertEqual(route["distance_m"], 250)

    def test_invalid_place(self):
        status, result = self.get_json(
            "/route?start=UNKNOWN&goal=CAFE"
        )
        self.assertEqual(status, 400)
        self.assertIn("error", result)

    def test_missing_closed_road_endpoint(self):
        status, result = self.get_json(
            "/route?start=GATE&goal=CAFE&closed_from=ADMIN"
        )
        self.assertEqual(status, 400)
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()