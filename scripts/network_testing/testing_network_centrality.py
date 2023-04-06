import osmnx as ox
import networkx as nx
import os
import sys
import pandas as pd

GRAPH_SETTINGS = {
    "simplified": {
        "simplify": True,
        "retain_all": False,
        "truncate_by_edge": False
    },
    "not_simplified": {
        "simplify": False,
        "retain_all": True,
        "truncate_by_edge": False
    },
    "not_truncated": {
        "simplify": False,
        "retain_all": True,
        "truncate_by_edge": True
    }
}

def get_graph(bbox, settings, walk_drive = None, custom_filter = None):
    if walk_drive:
        G = ox.graph.graph_from_bbox(bbox[0], bbox[1],bbox[2], bbox[3], network_type = walk_drive, simplify=settings["simplify"], retain_all=settings["retain_all"], truncate_by_edge = settings["truncate_by_edge"])
    else:
        G = ox.graph.graph_from_bbox(bbox[0], bbox[1],bbox[2], bbox[3], custom_filter = custom_filter, simplify=settings["simplify"], retain_all=settings["retain_all"], truncate_by_edge = settings["truncate_by_edge"])

    return G
'''
def get_graph_from_bb(bbox, walk_drive):
    G = ox.graph.graph_from_bbox(bbox[0], bbox[1],bbox[2], bbox[3], network_type = walk_drive, simplify=False, retain_all=True, truncate_by_edge = True)
    return G

def get_graph_from_bb_custom_filter(bbox, filter):
    G = ox.graph.graph_from_bbox(bbox[0], bbox[1],bbox[2], bbox[3], custom_filter = filter, simplify=False, retain_all=True, truncate_by_edge = True)
    return G
'''


def get_centrality(bbox, G):
    stats = {}
    G2 = nx.DiGraph(G)
    undirected_g = nx.to_undirected(G)

    basic_stats = ox.basic_stats(G)
    stats["circuity_avg"] = basic_stats['circuity_avg']

    stats["bet_centrality"] = avg(nx.betweenness_centrality(G2, normalized = True, endpoints=False))
    stats["pr_centrality"] = avg(nx.pagerank(G2))
    stats["eig_centrality"] = avg(nx.eigenvector_centrality(G2, max_iter=500))
    stats["deg_centrality"] = avg(nx.degree_centrality(G))
    stats["connected"] = nx.is_connected(undirected_g)
    stats["strongly_connected"] = nx.is_strongly_connected(G)
    stats["weakly_connected"] = nx.is_weakly_connected(G)

    return stats


def avg(evaluation_dictionary):
    vals = evaluation_dictionary.values()
    return sum(vals)/len(vals)

def create_stats_item(bbox, setting_type, type, filename):
    local_settings = GRAPH_SETTINGS[setting_type]
    if type == "custom_walk":
        G = get_graph(bbox, settings=local_settings, custom_filter='["highway"~"footway"]')
        stats = get_centrality(bbox, G)
    else:
        G = get_graph(bbox, settings=local_settings, walk_drive=type)
        stats = get_centrality(bbox, G)
    ox.plot.plot_graph(G, show=False, save= True, filepath = f".{filename}/{type}_{setting_type}.png")
    stats["type"] = type
    return stats

def get_centrality_comparisons(bbox, setting_type, filename):
    types = ["drive", "walk", "custom_walk"]
    stats = []
    if not os.path.isdir(filename):
        os.mkdir(f"./{filename}")
    for type in types:
        stats.append(create_stats_item(bbox, setting_type, type, filename))

    for item in stats:
        item["setting"] = setting_type

    return stats



def testing_loop(bbox, filename):
    stats = []
    for key, value in GRAPH_SETTINGS.items():
        stats += get_centrality_comparisons(bbox, key, filename)
    df = pd.DataFrame(stats)
    df.to_csv(f"{filename}.csv")
#Centrality tests

#N S E W


#1
testing_loop([47.65560, 47.65390,-122.34432, -122.34624], "case_1")

#2
testing_loop([47.6526, 47.6493,-122.3489, -122.3548], "case_2")

#3

testing_loop([47.67242, 47.67090, -122.27923, -122.28523], "case_3")

#4
testing_loop([47.67307, 47.67192, -122.28903, -122.29050], "case_4")

