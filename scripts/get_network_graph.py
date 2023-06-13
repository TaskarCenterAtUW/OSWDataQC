import osmnx as ox

def get_network_shapefile_for_place(city, filter, simplified, output_filename):
    G = ox.graph.graph_from_place(city, custom_filter = filter, simplify=simplified, retain_all=True)
    ox.io.save_graph_shapefile(G, filepath=f'''./{output_filename}_graph''', encoding='utf-8', directed=False)

get_network_shapefile_for_place("Bellevue, Washington, USA", '["highway"~"primary|secondary|tertiary|residential"]', True, "bellevue_streets_simplified")
get_network_shapefile_for_place("Seattle, Washington, USA", '["highway"~"primary|secondary|tertiary|residential"]', True, "seattle_streets_simplified")

get_network_shapefile_for_place("Bellevue, Washington, USA", '["highway"~"footway"]', False, "bellevue_sidewalks")
get_network_shapefile_for_place("Seattle, Washington, USA", '["highway"~"footway"]', False, "seattle_sidewalks")