import osmnx as ox
import networkx as nx
import os
import sys

def testing():
    graph = ox.graph.graph_from_xml(os.path.join(sys.path[0], "map_orig.osm"), bidirectional=False, simplify=True, retain_all=False)
    stats = ox.stats.edge_length_total(G = graph)
    print(stats)


def testing_compare():

    graph_drive = ox.graph.graph_from_bbox(47.6526, 47.6493,-122.3489, -122.3548, network_type = "drive", simplify=True, retain_all=False)
    print("driving graph created")
    stats_drive = ox.stats.edge_length_total(G = graph_drive)
    print(stats_drive)
    print(graph_drive)

    graph_walk = ox.graph.graph_from_bbox(47.6526, 47.6493,-122.3489, -122.3548, network_type = "walk", simplify=True, retain_all=False)
    print("walking graph created")
    stats_walk = ox.stats.edge_length_total(G = graph_walk)
    print(stats_walk)
    print(graph_walk)

def walking_street_length():
    graph_walk = ox.graph.graph_from_bbox(47.6526, 47.6493,-122.3489, -122.3548, network_type = "walk", simplify=True, retain_all=False)
    print("walking graph created")
    graph_walk_undirected = ox.utils_graph.get_undirected(G=graph_walk)
    stats_walk = ox.stats.street_length_total(Gu = graph_walk_undirected)
    print(stats_walk)


def get_graph_from_bb(bbox, walk_drive):
    G = ox.graph.graph_from_bbox(bbox[0], bbox[1],bbox[2], bbox[3], network_type = walk_drive, simplify=True, retain_all=False)
    return G


def get_centrality(bbox, walk_drive):
    
    G = get_graph_from_bb(bbox, walk_drive)
    basic_stats = ox.basic_stats(G)
    print("circuity avg: ")
    print(basic_stats['circuity_avg'])

    G2 = nx.DiGraph(G)

    #extended_stats = ox.extended_stats(G, bc=True)
    print("betweenness centrality: ")
    bet_centrality = nx.betweenness_centrality(G2, normalized = True, endpoints=False)
    #print(bet_centrality)
    print(avg(bet_centrality))

    print("page rank")
    pr_centrality = nx.pagerank(G2)
    #print(pr_centrality)
    print(avg(pr_centrality))

def avg(evaluation_dictionary):
    vals = evaluation_dictionary.values()
    return sum(vals)/len(vals)

def get_centrality_comparisons(bbox):
    print("walking stats")
    print("--------")
    get_centrality(bbox, "walk")
    print("driving stats")
    print("--------")
    get_centrality(bbox, "drive")




#Centrality tests
#get_centrality_comparisons([47.6526, 47.6493,-122.3489, -122.3548])

#get_centrality_comparisons([47.65560, 47.65390,-122.34432, -122.34624])

#get_centrality_comparisons([47.75988, 47.75765, -122.34003, -122.34333])


# Network length tests
#testing_compare()
#walking_street_length()
#testing()

#Output
'''
https://www.openstreetmap.org/export#map=16/47.6513/-122.3515&layers=T
'''
'''
testing output:
44291.670999999944
'''

'''
testing compare Output:

driving graph created
3192.9599999999996

MultiDiGraph with 15 nodes and 35 edges

walking graph created
18033.777999999988

walking
MultiDiGraph with 243 nodes and 730 edges


'''

'''
walking st length output
9016.889000000005
'''