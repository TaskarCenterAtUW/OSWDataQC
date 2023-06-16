import os
os.environ['USE_PYGEOS'] = '0'
import networkx as nx
import geopandas as gpd
import os
import osmnx as ox
import dask_geopandas
from statistics import stdev


def func( feature ):
    poly = feature.geometry
    if (poly.geom_type == "Polygon" or poly.geom_type == "MultiPolygon"):
        measures = get_measures_from_polygon(poly)
        feature.betweenness_stdev = measures["betweenness_stdev"]
        return feature

def analyze_area(filename, path = 'pwd'):
    if path == 'pwd':
        path = os.getcwd()

    gdf = gpd.read_file(os.path.join(path, (filename + '.geojson')))
    gdf['betweenness_stdev'] = None
    
    df_dask = dask_geopandas.from_geopandas(gdf, npartitions=16)  
    if __name__ == '__main__':
        output = df_dask.apply(func, axis=1, meta=[
            ('OBJECTID','int64'), 
            ('Shape_Length', 'float64'), 
            ('Shape_Area','float64'), 
            ('Input_FID','int64'), 
            ('geometry', 'geometry'), 
            ('betweenness_stdev', 'object'), 
            ]).compute(scheduler='multiprocessing')
        
        output.to_file(os.path.join(path, (filename + '_betweenness_stdev.shp')))

    
def get_measures_from_polygon(polygon):
    try:
        G = ox.graph.graph_from_polygon(polygon, custom_filter = '["highway"~"footway"]', truncate_by_edge=True, simplify=False, retain_all=True)
    except Exception as e:
        print(f"Unexpected {e}, {type(e)} with polygon {polygon} when getting graph")
        return {"betweenness_stdev": None}
    stats = get_centrality(G, polygon)
    return stats

def get_centrality(G, polygon):
    stats = {}
    undirected_g = nx.Graph(G)

    bet = nx.betweenness_centrality(undirected_g, normalized = True, endpoints=False)

    stats["betweenness_stdev"] = stdev(bet.values())
    return stats



analyze_area("seattle_new_tiling", "C:\\Users\\jessica\\Documents\\ArcGIS\\Projects\\MappingSidewalkMetrics\\")