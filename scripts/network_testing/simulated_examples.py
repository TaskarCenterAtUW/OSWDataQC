import networkx as nx
import matplotlib.pyplot as plt
import csv

cases = {
    1:
    {
        "nodes": { 1: (1,1), 2: (2,1), 3: (3,1), 4: (3,2), 5: (2,2), 6: (1,2)},
        "edges": [(1,2), (2,3), (3,4), (4,5), (5,6), (6,1), (2,5)]
    }
}

def create_graph(case_number):
    G=nx.Graph()
    for node_number, node_coordinates in cases[case_number]["nodes"].items():
        G.add_node(node_number,pos=node_coordinates)
    for edge in cases[case_number]["edges"]:
        G.add_edge(edge[0], edge[1])
    
    draw_graph(G, f"original_case_{case_number}.png")
    return G


def get_calculations():
    centrality_stats = {}
    for case_number, case in cases.items():
        G = create_graph(case_number)
        edge_stats = edge_calculations(case, G, case_number)
        node_stats = node_calculations(case, G, case_number)
        centrality_stats[case_number] = {
            "edge_stats": edge_stats,
            "node_stats": node_stats
        }
        #save lists to csv
        save_csv(edge_stats, f"edge_{case_number}.csv")
        save_csv(node_stats, f"node_{case_number}.csv")

def save_csv(list_of_dict,filename):
    with open(filename, 'w') as csvfile: 
        csvwriter = csv.writer(csvfile) 
        csvwriter.writerow(list_of_dict[0].keys())
        for row in list_of_dict:
            csvwriter.writerow(row.values())

def edge_calculations(case, G, case_number):
    original_centrality_stats = get_centrality(G)
    original_centrality_stats["broken_edge"]="none"
    stats = [original_centrality_stats]
    for edge in case["edges"]:
        print(edge)
        node_1,node_2 = break_edge(edge, G)
        draw_graph(G, f"case_{case_number}_broken_edge_{edge}.png")
        edge_stats = get_centrality(G)
        edge_stats["broken_edge"] = edge
        stats.append(edge_stats)
        # add centrality metrics to list
        connect_edge(G, edge, node_1, node_2)
        #draw_graph(G)
    return stats

def draw_graph(G, filename):
    fig = plt.figure()
    pos=nx.get_node_attributes(G,'pos')
    nx.draw(G,pos,ax=fig.add_subplot())
    fig.savefig(filename)
    #plt.show()

def draw_graph_without_geo(G, filename):
    fig = plt.figure()
    nx.draw(G,ax=fig.add_subplot())
    fig.savefig(filename)
    #plt.show()

def break_edge(edge_tuple, G):
    node_1 = edge_tuple[0]
    node_2 = edge_tuple[1]
    midpoint = (G.nodes[node_1]['pos'][0] + G.nodes[node_2]['pos'][0]) / 2, \
           (G.nodes[node_1]['pos'][1] + G.nodes[node_2]['pos'][1]) / 2
    
    print(midpoint)
    # Calculate the coordinates of the two new nodes
    dist = .1  # Distance from the midpoint
    new_pos1 = ((midpoint[0] + dist * (G.nodes[node_2]['pos'][0] - G.nodes[node_1]['pos'][0]) / 2),
            (midpoint[1] + dist * (G.nodes[node_2]['pos'][1] - G.nodes[node_1]['pos'][1]) / 2))
    new_pos2 = ((midpoint[0] - dist * (G.nodes[node_2]['pos'][0] - G.nodes[node_1]['pos'][0]) / 2),
            (midpoint[1] - dist * (G.nodes[node_2]['pos'][1] - G.nodes[node_1]['pos'][1]) / 2))
    # Add the new nodes to the graph and connect them to the original endpoints of the edge
    new_node1 = max(G.nodes) + 1
    new_node2 = new_node1 + 1

    G.remove_edge(node_1, node_2)
    
    G.add_node(new_node1, pos=new_pos1)
    G.add_node(new_node2, pos=new_pos2)
    G.add_edge(node_2, new_node1)
    G.add_edge(new_node2, node_1)

    return new_node1, new_node2

def connect_edge(G, edge_tuple, node_1, node_2):
    G.remove_node(node_1)
    G.remove_node(node_2)
    G.add_edge(edge_tuple[0],edge_tuple[1])


def node_calculations(case, G, case_number):
    original_centrality_stats = get_centrality(G)
    original_centrality_stats["broken_node"]="none"
    stats = [original_centrality_stats]
    for node_number, node in case["nodes"].items():
        edge_list, node_list = break_node(case["edges"], node, node_number, G)
        node_stats = get_centrality(G)
        node_stats["broken_node"] = node_number
        stats.append(node_stats)
        draw_graph(G, f"case_{case_number}_broken_node_{node_number}.png")
        draw_graph_without_geo(G, f"case_{case_number}_broken_node_{node_number}_no_geo.png")
        connect_node(edge_list, node_list, G, node_number, node)
        #draw_graph(G)
    return stats

def break_node(edges, node, node_number, G):
    edges_with_node = []
    new_node_list = []
    for edge in edges:
        if node_number in edge:
            new_node = max(G.nodes) + 1
            G.add_node(new_node, pos=node)
            for node_iter in edge:
                if node_iter != node_number:
                    G.add_edge(node_iter,new_node)
            edges_with_node.append(edge)
            new_node_list.append(new_node)
    G.remove_node(node_number)
    #draw_graph(G)
    return edges_with_node, new_node_list
    # return new node list

def connect_node(edge_list, node_list, G, node_orig, node_orig_coordinates):
    for node_to_delete in node_list:
        G.remove_node(node_to_delete)
    G.add_node(node_orig,pos=node_orig_coordinates)
    for edge in edge_list:
        G.add_edge(edge[0], edge[1])
    
    # reconect all edges for node

def get_centrality(G):
    stats = {}
    undirected_g = nx.Graph(G)

    bet = nx.betweenness_centrality(undirected_g, normalized = True, endpoints=False)
    eigen = nx.eigenvector_centrality(undirected_g, max_iter=2000)
    deg = nx.degree_centrality(undirected_g)
    stats["bet_centrality_avg"] = avg(bet)
    stats["eig_centrality_avg"] = avg(eigen)
    stats["deg_centrality_avg"] = avg(deg)
    stats["connected"] = nx.is_connected(undirected_g)

    return stats

def avg(evaluation_dictionary):
    vals = evaluation_dictionary.values()
    return sum(vals)/len(vals)

get_calculations()


