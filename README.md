# BuildRoutePlanner

A campus route planner that finds the shortest walking route between two places. The map is stored in CSV files, the routing engine is written in C++, and a small Python HTTP API exposes route queries.

## Features

- Finds minimum-distance routes using Dijkstra's algorithm
- Shows the total distance, path, and step-by-step directions
- Recalculates a route when one road is temporarily closed
- Serves routes, place IDs, and health information over HTTP
- Caches API responses and changes the cache key when the map files change

## Files

| File | Purpose |
| --- | --- |
| `nodes.csv` | Place IDs, names, and coordinates |
| `edges.csv` | Roads, distances, and road names |
| `main.cpp` | Loads the map and calculates routes |
| `api.py` | HTTP API and response cache |
| `test_routes.py` | Tests the C++ routing engine |
| `test_api.py` | Tests API requests and caching |

## Build and run

You need a C++ compiler and Python 3. Run these commands from the project folder in PowerShell:

```powershell
g++ -std=c++14 -Wall -Wextra main.cpp -o main.exe
.\main.exe
```

Enter place IDs when prompted. For example, enter `GATE` as the start and `CAFE` as the destination. Press Enter at the closed-road prompt to leave all roads open.

To run the automated checks:

```powershell
python test_routes.py
python test_api.py
```

## HTTP API

Build `main.exe` first, then start the API:

```powershell
python api.py
```

Open these URLs in your browser:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/places`
- `http://127.0.0.1:8000/route?start=GATE&goal=CAFE`
- `http://127.0.0.1:8000/route?start=GATE&goal=CAFE&closed_from=ADMIN&closed_to=CAFE`

The route endpoint returns JSON containing reachability, distance in metres, the path, directions, map version, and whether the result came from the cache.

## How it works

The program reads places and roads from the CSV files and builds an adjacency list. Each road is added in both directions. Dijkstra's algorithm uses a priority queue to find the minimum total distance; parent nodes reconstruct the route afterward. A temporary closure skips the selected road during the search.

The API validates place IDs, runs the C++ engine for an uncached request, and stores its response in memory. Its cache key includes the route, optional closure, and a hash of the map files.

For a graph with `V` places and `E` roads, the routing algorithm takes approximately `O((V + E) log V)` time and `O(V + E)` space.

## Limitations

The included campus map is fictional. The API starts the C++ program for each uncached request and reads its text output, which adds process startup cost. The cache is in memory and clears when the API stops.