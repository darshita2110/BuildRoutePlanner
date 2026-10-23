import csv
import hashlib
import json
import re
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "main.exe"
NODES = ROOT / "nodes.csv"
EDGES = ROOT / "edges.csv"

cache = {}
cache_lock = Lock()
MAX_CACHE_ENTRIES = 256


def map_version():
    digest = hashlib.sha256()
    digest.update(NODES.read_bytes())
    digest.update(EDGES.read_bytes())
    return digest.hexdigest()[:12]


def place_ids():
    with NODES.open(newline="", encoding="utf-8") as file:
        return {row["id"] for row in csv.DictReader(file)}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, value):
        data = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        request = urlsplit(self.path)
        query = parse_qs(request.query)

        if request.path == "/health":
            self.send_json(200, {"status": "ok", "map_version": map_version()})
            return

        if request.path == "/places":
            self.send_json(200, {"places": sorted(place_ids())})
            return

        if request.path != "/route":
            self.send_json(404, {"error": "Endpoint not found"})
            return

        start = query.get("start", [""])[0]
        goal = query.get("goal", [""])[0]
        closed_from = query.get("closed_from", [""])[0]
        closed_to = query.get("closed_to", [""])[0]

        ids = place_ids()
        if start not in ids or goal not in ids:
            self.send_json(400, {"error": "Unknown start or destination ID"})
            return

        if bool(closed_from) != bool(closed_to):
            self.send_json(400, {"error": "Supply both closed-road endpoints"})
            return

        if closed_from and (closed_from not in ids or closed_to not in ids):
            self.send_json(400, {"error": "Unknown closed-road endpoint"})
            return

        version = map_version()
        key = (version, start, goal, closed_from, closed_to)

        with cache_lock:
            saved = cache.get(key)

        if saved is not None:
            self.send_json(200, {**saved, "cached": True})
            return

        user_input = f"{start}\n{goal}\n{closed_from}\n"
        if closed_from:
            user_input += f"{closed_to}\n"

        try:
            run = subprocess.run(
                [str(ENGINE)],
                input=user_input,
                text=True,
                capture_output=True,
                cwd=ROOT,
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            self.send_json(504, {"error": "Routing engine timed out"})
            return
        except OSError as error:
            self.send_json(503, {"error": f"Cannot start routing engine: {error}"})
            return

        if run.returncode != 0:
            self.send_json(400, {"error": run.stderr.strip() or "Route query failed"})
            return

        distance_match = re.search(
            r"Shortest\s+Distance:\s*(\d+)\s*m",
            run.stdout,
            re.IGNORECASE,
        )

        if distance_match is None:
            if "No route found" in run.stdout:
                result = {
                    "reachable": False,
                    "distance_m": None,
                    "path": [],
                    "directions": [],
                    "map_version": version,
                }
            else:
                self.send_json(502, {"error": "Unexpected routing engine output"})
                return
        else:
            path_match = re.search(r"^Path:\s*(.+)$", run.stdout, re.MULTILINE)
            path = path_match.group(1).split(" -> ") if path_match else []
            directions = re.findall(r"^\s*\d+\.\s+(.+)$", run.stdout, re.MULTILINE)

            result = {
                "reachable": True,
                "distance_m": int(distance_match.group(1)),
                "path": path,
                "directions": directions,
                "map_version": version,
            }

        with cache_lock:
            if len(cache) >= MAX_CACHE_ENTRIES:
                cache.clear()
            cache[key] = result

        self.send_json(200, {**result, "cached": False})


if __name__ == "__main__":
    if not ENGINE.exists():
        raise SystemExit("Build main.exe before starting the API")

    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Route API running at http://127.0.0.1:8000")
    server.serve_forever()