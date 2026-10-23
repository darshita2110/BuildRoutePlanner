#include<fstream>
#include<iostream>
#include<sstream>
#include<stdexcept>
#include<string>
#include<vector>
#include<unordered_map>
#include<algorithm>
#include<functional>
#include<limits>
#include<queue>
#include<utility>
using namespace std;

struct Node{
    string id;
    string name;
    double x;
    double y;
};
struct Edge {
    int to;
    double distance;
    string roadName;
};
struct Route{
    vector<int> path;
    double distance = numeric_limits<double>::infinity();
};

vector<string> splitCsv(const string& line) {
    vector<string> fields;
    string field;
    istringstream input(line);

    while(getline(input, field, ',')) {
        fields.push_back(field);
    }

    return fields;
}

class Graph {
    private :
        vector<Node> nodes;
        vector<vector<Edge>> adjacency; // directs road leaving each node
        unordered_map<string, int> idToIndex;

    public :
        void loadNodes(const string& filename) {
            ifstream file(filename);
            if(!file) {
                throw runtime_error("Cannot open " + filename);
            }

            string line;
            getline(file, line);
            while(getline(file, line)) {
                if(line.empty()) continue;

                vector<string> fields = splitCsv(line);
                if(fields.size() != 4) {
                    throw runtime_error("A node must have 4 fields");
                }

                Node node{
                    fields[0],
                    fields[1],
                    stod(fields[2]),
                    stod(fields[3])
                };

                if(idToIndex.count(node.id)) {
                    throw runtime_error("Duplicate node ID: " + node.id);
                }

                idToIndex[node.id] = static_cast<int>(nodes.size());
                nodes.push_back(node);
                adjacency.emplace_back(); // add an empty vector for edges
            }
        }

        void loadEdges(const string& filename) {
            ifstream file(filename);
            if(!file) {
                throw runtime_error("Cannot open " + filename);
            }

            string line;
            getline(file, line);
            while(getline(file, line)) {
                if(line.empty()) continue;

                vector<string> fields = splitCsv(line);
                if(fields.size() != 4) {
                    throw runtime_error("An edge row must have 4 fields");
                }
                auto fromIt = idToIndex.find(fields[0]);
                auto toIt = idToIndex.find(fields[1]);

                if(fromIt == idToIndex.end() || toIt == idToIndex.end()) {
                    throw runtime_error("Road refers to an unknown noded ID");
                }
                double distance = stod(fields[2]);
                if(distance <= 0) {
                    throw runtime_error("Distance must be positive");
                }
                int from = fromIt->second;
                int to = toIt->second;    

                adjacency[from].push_back({to, distance, fields[3]});
                adjacency[to].push_back({from, distance, fields[3]});         
            }
        }

        void printNodes() const {
            for(const Node& node : nodes) {
                cout<< node.id << " -> " << node.name << " (" << node.x << ", " << node.y << ")\n";
            }
        }

        void printRoads() const {
            for(size_t i = 0; i < nodes.size(); i++) {
                cout<< nodes[i].id<< "\n";
                for(const Edge& road : adjacency[i]) {
                    cout << " -> " << nodes[road.to].id 
                    << " (" << road.distance << " m via " 
                    << road.roadName << ")\n";
                }
            }
        }

        int findNode(const string& id) {
            auto it = idToIndex.find(id);
            if(it == idToIndex.end()) {
                return -1;
            }
            return it->second;
        }

        Route shortestPath(int start, int goal) const {
            const double INF = numeric_limits<double>::infinity();
            vector<double> dist(nodes.size(), INF);
            vector<int> parent(nodes.size(), -1);
            using Entry = pair<double, int>;
            priority_queue<Entry, vector<Entry>, greater<Entry>> pq;

            dist[start] = 0;
            pq.push({0, start});
            while(!pq.empty()) {
                Entry topEntry = pq.top();
                double currentDist = topEntry.first;
                int u = topEntry.second;
                pq.pop();
                if(currentDist > dist[u]) continue;
                if(u == goal) break;

                for(const Edge& road : adjacency[u]) {
                    double candidate = dist[u] + road.distance;

                    if(candidate < dist[road.to]) {
                        dist[road.to] = candidate;
                        parent[road.to] = u;
                        pq.push({candidate, road.to});
                    }
                }
            }
            if(dist[goal] == INF) return {};

            Route result;
            result.distance = dist[goal];   
            for(int at = goal; at != -1; at = parent[at]) {
                result.path.push_back(at);
            }   
            reverse(result.path.begin(), result.path.end());
            return result;         
        }
        string placeName(int index) const {
            return nodes.at(index).name;
    }

    void printDirections(const Route& route) const {
        for(size_t i = 1; i < route.path.size(); i++) {
            int from = route.path[i - 1];
            int to = route.path[i];

            for(const Edge& road : adjacency[from]) {
                if(road.to == to) {
                    cout << i << ". Take " << road.distance << " m via " << road.roadName <<
                    " for " << road.distance << " m from " <<
                    nodes[from].name << " to " << nodes[to].name << ".\n";
                    break;
                }
            }
        }
    }

};

int main() {
    try {
        Graph graph;
        graph.loadNodes("nodes.csv");
        graph.loadEdges("edges.csv");
        string startId, goalId;

        cout << "Start ID: ";
        getline(cin, startId);

        cout << "Destination ID: ";
        getline(cin, goalId);

        int start = graph.findNode(startId);
        int goal = graph.findNode(goalId);

        if(start == -1 || goal == -1) {
            throw runtime_error("Unknown start or end");
        }
        Route route = graph.shortestPath(start, goal);
        if(route.path.empty()) {
            cout<<"No route found\n";
        }
        else {
            cout<<"Shortest Distance: "<< route.distance << "m\n";
            cout<< "Path: ";
            for (size_t i = 0; i < route.path.size(); ++i) {
                if (i > 0) cout << " -> ";
                cout << graph.placeName(route.path[i]);
            }
            cout<<"\n";
            cout << "Directions:\n";
            graph.printDirections(route);
            
        }
        graph.printNodes();
        graph.printRoads();
        
    }
    catch (const exception& error) {
        cerr << "Error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}