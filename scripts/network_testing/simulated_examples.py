import networkx as nx
import matplotlib.pyplot as plt
import csv
import os

cases = {
    1:
    {
        "nodes": { 1: (1,1), 2: (2,1), 3: (3,1), 4: (3,2), 5: (2,2), 6: (1,2)},
        "edges": [(1,2), (2,3), (3,4), (4,5), (5,6), (6,1), (2,5)]
    },
    2: {
        "nodes": { 1: (1,1), 2: (2,1), 3: (3,1), 4: (3,2), 5: (2,2), 6: (1,2)},
        "edges": [(1,2), (2,3), (3,4), (4,5), (5,6), (6,1)]
    },
    3: {
        "nodes": { 1: (1,1), 2: (2,1), 3: (3,1), 4: (3,2), 5: (2,2), 6: (1,2), 7: (3,4), 8: (4,4)},
        "edges": [(1,2), (2,3), (3,4), (4,5), (5,6), (6,1), (7,8)]
    },
    4: {
        "nodes": { 1: (1,1), 2: (2,1), 3: (3,1), 4: (3,2), 5: (2,2), 6: (1,2), 7: (3,3), 8: (3,4), 9:(2,4)},
        "edges": [(1,2), (2,3), (3,4), (4,5), (5,6), (6,1), (4,7), (7,8),(8,9),(9,4)]
    },
    5: {
        "nodes": {1: (2,2), 2: (1,2), 3: (1.25,2.75), 4: (2,3), 5: (2.75,2.75), 6: (3,2), 7: (2.75,1.25), 8: (2,1), 9: (1.25,1.25) },
        "edges": [(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,2), (1,2), (1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9)]
    },
    6: {
        "nodes": {1: (1,1), 2: (1,2), 3: (1,3), 4:(2,3), 5: (2,2), 6: (2,1), 7: (3,1), 8: (3,2), 9: (3,3), 10: (4,1)},
        "edges": [(1,2), (2,3), (3,4), (4,9), (9,8), (8,7), (7,6), (6,1), (1,10), (4,5), (5,8) ]
    }
}

def create_graph(case_number):
    G=nx.Graph()
    for node_number, node_coordinates in cases[case_number]["nodes"].items():
        G.add_node(node_number,pos=node_coordinates)
    for edge in cases[case_number]["edges"]:
        G.add_edge(edge[0], edge[1])
    
    draw_graph(G, f"case_{case_number}/original.png")
    return G


def get_calculations():
    centrality_stats = {}
    for case_number, case in cases.items():
        if not os.path.isdir(f"./case_{case_number}"):
            os.mkdir(f"./case_{case_number}")
        G = create_graph(case_number)
        edge_stats = edge_calculations(case, G, case_number)
        node_stats = node_calculations(case, G, case_number)
        centrality_stats[case_number] = {
            "edge_stats": edge_stats,
            "node_stats": node_stats
        }
        #save lists to csv
        save_csv(edge_stats, f"case_{case_number}/edge_{case_number}.csv")
        save_csv(node_stats, f"case_{case_number}/node_{case_number}.csv")

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
        #print(edge)
        node_1,node_2 = break_edge(edge, G)
        draw_graph(G, f"case_{case_number}/broken_edge_{edge}.png")
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
    nx.draw(G,pos,ax=fig.add_subplot(), with_labels = True)
    fig.savefig(filename)
    #plt.show()

def draw_graph_without_geo(G, filename):
    fig = plt.figure()
    nx.draw(G,ax=fig.add_subplot(), with_labels = True)
    fig.savefig(filename)
    #plt.show()

def break_edge(edge_tuple, G):
    node_1 = edge_tuple[0]
    node_2 = edge_tuple[1]
    midpoint = (G.nodes[node_1]['pos'][0] + G.nodes[node_2]['pos'][0]) / 2, \
           (G.nodes[node_1]['pos'][1] + G.nodes[node_2]['pos'][1]) / 2
    
    #print(midpoint)
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
        if len(edge_list) > 1:
            node_stats = get_centrality(G)
            node_stats["broken_node"] = node_number
            stats.append(node_stats)
            draw_graph(G, f"case_{case_number}/broken_node_{node_number}.png")
            draw_graph_without_geo(G, f"case_{case_number}/broken_node_{node_number}_no_geo.png")
        connect_node(edge_list, node_list, G, node_number, node)
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

    return edges_with_node, new_node_list


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


