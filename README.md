## Architecture

The C++ routing engine loads the CSV map into an adjacency list and uses
Dijkstra's algorithm to find minimum-distance paths. A Python standard-library
HTTP service validates requests, calls the routing engine, and caches responses.
The cache key includes a hash of both map files, the route endpoints, and the
optional closed road, so edited map data does not reuse an older cached answer.

## API

- `GET /health` — service status and map version
- `GET /places` — available place IDs
- `GET /route?start=GATE&goal=CAFE` — shortest route
- `GET /route?start=GATE&goal=CAFE&closed_from=ADMIN&closed_to=CAFE`
  — route with one temporarily closed road

Run `python api.py`, then visit `http://127.0.0.1:8000/health`.

## Current limitations

The sample map is fictional. The API starts the C++ executable for each
uncached request, which adds process-startup cost. This local prototype uses
an in-memory cache, so cached entries disappear when the API restarts.