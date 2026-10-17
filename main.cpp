#include<fstream>
#include<iostream>
#include<sstream>
#include<stdexcept>
#include<string>
#include<vector>
#include<unordered_map>
using namespace std;

struct Node{
    string id;
    string name;
    double x;
    double y;
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
            }
        }

        void printNodes() const {
            for(const Node& node : nodes) {
                cout<< node.id << " -> " << node.name << " (" << node.x << ", " << node.y << ")\n";
            }
        }
};

int main() {
    try {
        Graph graph;
        graph.loadNodes("nodes.csv");
        graph.printNodes();
    }
    catch (const exception& error) {
        cerr << "Error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}