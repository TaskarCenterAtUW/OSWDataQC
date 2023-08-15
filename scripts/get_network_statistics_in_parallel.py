import os
os.environ['USE_PYGEOS'] = '0'
import networkx as nx
import geopandas as gpd
import os
import osmnx as ox
import dask_geopandas
from statistics import stdev, mean


def func( feature ):
    poly = feature.geometry
    if (poly.geom_type == "Polygon" or poly.geom_type == "MultiPolygon"):
        measures = get_measures_from_polygon(poly)
        feature.degree = measures["deg_centrality_avg"]
        feature.eigen = measures["eig_centrality_avg"]
        feature.betweenness = measures["bet_centrality_avg"]
        feature.bet_stdev = measures["bet_stdev"]
        return feature

def analyze_area(filename, path = 'pwd'):
    if path == 'pwd':
        path = os.getcwd()

    gdf = gpd.read_file(os.path.join(path, (filename + '.geojson')))
    gdf['degree'] = None
    gdf['betweenness'] = None
    gdf['eigen'] = None
    gdf['bet_stdev'] = None
    
    df_dask = dask_geopandas.from_geopandas(gdf, npartitions=16)  
    if __name__ == '__main__':
        output = df_dask.apply(func, axis=1, meta=[
            ('OBJECTID', 'int64'),
            ('Shape_Length', 'float64'),
            ('Shape_Area','float64'), 
            ('Input_FID','int64'), 
            ('geometry', 'geometry'),
            ('degree','object'),
            ('betweenness', 'object'), 
            ('eigen', 'object'),
            ('bet_stdev', 'object'),
            ]).compute(scheduler='multiprocessing')
        
        print("outputting file")
        
        output.to_file(os.path.join("C:\\Development\\tdei\\outputs", (filename + '_all_measures.shp')))

    
def get_measures_from_polygon(polygon):
    try:
        G = ox.graph.graph_from_polygon(polygon, custom_filter = '["highway"~"footway|steps"]', truncate_by_edge=True, simplify=False, retain_all=True)
    except Exception as e:
        print(f"Unexpected {e}, {type(e)} with polygon {polygon} when getting graph")
        return {"bet_centrality_avg": None,"eig_centrality_avg": None,"deg_centrality_avg": None, "bet_stdev": None}
    stats = get_centrality(G, polygon)
    return stats

def get_centrality(G, polygon):
    stats = {}
    undirected_g = nx.Graph(G)

    bet = nx.betweenness_centrality(undirected_g, normalized = True, endpoints=False)
    try:
        eigen = nx.eigenvector_centrality(undirected_g, max_iter=1000)
        stats["eig_centrality_avg"] = mean(eigen.values())
    except Exception as e:
        print(f"Unexpected {e}, {type(e)} with polygon {polygon} when getting eigen value")
        stats["eig_centrality_avg"] = None

    deg = nx.degree_centrality(undirected_g)
    stats["bet_centrality_avg"] = mean(bet.values())
    stats["deg_centrality_avg"] = mean(deg.values())
    stats["bet_stdev"] = stdev(bet.values())
    return stats

analyze_area("redmond_new_tiling","C:\\Users\\jessica\\Documents\\work\\redmond")
#analyze_area("seattle_new_tiling","C:\\Users\\jessica\\Documents\\ArcGIS\\Projects\\MappingSidewalkMetrics")
#analyze_area("seattle_crossing_tasks", "C:\\Development\\tdei\\OSWDataQC")
#analyze_area("bellevue_crossing_tasks", "C:\\Development\\tdei\\OSWDataQC")
#analyze_area("seattle_sidewalk_tasks", "C:\\Development\\tdei\\OSWDataQC")
#analyze_area("bellevue_sidewalk_tasks", "C:\\Development\\tdei\\OSWDataQC")