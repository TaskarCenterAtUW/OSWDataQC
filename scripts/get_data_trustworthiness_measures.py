import os
os.environ['USE_PYGEOS'] = '0'
import networkx as nx
import geopandas as gpd
import os
import osmnx as ox
import dask_geopandas
import osmnx as ox
from util.osm_bb_data import get_item_history_from_id
from datetime import datetime
import geonetworkx as gnx
from shapely.ops import voronoi_diagram
from shapely.geometry import box

#TODO: make date, projection, and tiling filepath an input 
DATE = datetime.strptime("2023-07-01T19:20:00Z", "%Y-%m-%dT%H:%M:%SZ")
#DATE = datetime.now() 
SIDEWALK_FILTER = '["highway"~"footway|steps|living_street|path"]'
PROJ = 'epsg:26910' 
TILING_FILEPATH = "C:\\Users\\jessica\\Downloads\\redmond_crossing_tasks.geojson"
#TILING_FILEPATH = "C:\\Users\\jessica\\Documents\\ArcGIS\\Projects\\SeattleIndexing\\Fremont Tiling.geojson"

def main(city):
    if __name__ == "__main__":
        ox.config(overpass_settings = '[out:json][timeout:{timeout}][date:"' + datetime.strftime(DATE, "%Y-%m-%dT%H:%M:%SZ") + '"]')
        # for a city
        get_city_data(city)

def main_bbox(n,s,e,w):
    if __name__ == "__main__":
        ox.config(overpass_settings = '[out:json][timeout:{timeout}][date:"' + datetime.strftime(DATE, "%Y-%m-%dT%H:%M:%SZ") + '"]')
        # for a bounding box
        get_bbox_data(n,s,e,w)

def get_city_data(city):
    G_sidewalk = get_street_network(city, SIDEWALK_FILTER)
    gdf_pois = ox.features.features_from_place(city,  tags = {'amenity': True} )
    gdf_bldgs = ox.features.features_from_place(city,  tags = {'building': True} )
    G_roads = ox.graph.graph_from_place(city, network_type = 'drive', simplify=False, retain_all=True)
    gdf_roads = gnx.graph_edges_to_gdf(G_roads).to_crs({'init': PROJ})

    G_roads_simplified = ox.graph.graph_from_place(city, network_type = 'drive', simplify=True, retain_all=True)

    gdf_roads_simplified = gnx.graph_edges_to_gdf(G_roads_simplified).to_crs({'init': PROJ})
    
    
    perform_calculations(G_sidewalk, gdf_pois, gdf_bldgs, gdf_roads, gdf_roads_simplified)
    return 

def create_voronoi_diagram(gdf_roads_simplified):
    # first thin the nodes
    voronoi = voronoi_diagram(gdf_roads_simplified.boundary.cascaded_union, tolerance=100)
    voronoi_gdf = gpd.GeoDataFrame(index=[0], crs=PROJ, geometry=[voronoi])
    return voronoi_gdf

def get_bbox_data(n,s,e,w):
    G_sidewalk = get_street_network_from_bbox(n,s,e,w, SIDEWALK_FILTER)
    gdf_pois = ox.features.features_from_bbox(n,s,e,w, tags = {'amenity': True}).to_crs({'init': PROJ})
    gdf_bldgs = ox.features.features_from_bbox(n,s,e,w, tags = {'building': True}).to_crs({'init': PROJ})
    G_roads = ox.graph.graph_from_bbox(n,s,e,w, network_type = 'drive', simplify=False, retain_all=True)

    gdf_roads = gnx.graph_edges_to_gdf(G_roads).to_crs({'init': PROJ})

    G_roads_simplified = ox.graph.graph_from_bbox(n,s,e,w, network_type = 'drive', simplify=True, retain_all=True)

    gdf_roads_simplified = gnx.graph_edges_to_gdf(G_roads_simplified).to_crs({'init': PROJ})
    
    
    perform_calculations(G_sidewalk, gdf_pois, gdf_bldgs, gdf_roads, gdf_roads_simplified)
    
    return 

def perform_calculations(G_sidewalk, gdf_pois, gdf_bldgs, gdf_roads, gdf_roads_simplified):
    
    trust_measures_by_sidewalk = analyze_sidewalk_data(G_sidewalk, gdf_pois, gdf_bldgs, gdf_roads)
    #tiling = create_voronoi_diagram(gdf_roads_simplified)
    #tiling = tiling.geometry.explode()
    #tiling.to_file(os.path.join("C:\\Development\\tdei\\outputs\\test", ('redmond_tilng.shp'))) #TODO: make this name dynamic
    trust_measures_by_sidewalk.to_csv(os.path.join("C:\\Development\\tdei\\outputs\\test", ('redmond_trust_by_sidewalk_july.csv')))
    trust_measures_by_sidewalk.to_file(os.path.join("C:\\Development\\tdei\\outputs\\test", ('redmond_trust_by_sidewalk_july.shp')))

    trust_by_tile_gdf = get_trust_by_tile(trust_measures_by_sidewalk)

    print("trust by sidewalk")

    trust_by_tile_gdf.to_csv(os.path.join("C:\\Development\\tdei\\outputs\\test", ('redmond_trust_by_tile_gdf_july.csv')))
    trust_by_tile_gdf.to_file(os.path.join("C:\\Development\\tdei\\outputs\\test", ('redmond_trust_by_tile_july.shp'))) #TODO: make this name dynamic
    


def get_trust_by_tile(trust_measures_by_sidewalk_gdf):

    tiles_gdf = gpd.read_file(TILING_FILEPATH).to_crs({'init': PROJ})
    tiles_with_sidewalks_gdf = gpd.sjoin(tiles_gdf, trust_measures_by_sidewalk_gdf, how='inner', predicate='intersects')
    trust_by_tile = tiles_with_sidewalks_gdf.groupby('index_left').agg( 
        {'trust_score': 'mean'}) 
    
    trust_by_tile_gdf = tiles_gdf.merge(trust_by_tile, left_on="index", right_on="index_left")
    
    return trust_by_tile_gdf


def get_street_network(city, filter):
    G = ox.graph.graph_from_place(city, custom_filter = filter, simplify=False, retain_all=True)
    return G

def get_street_network_from_bbox(n,s,e,w, filter):
    G = ox.graph.graph_from_bbox(n,s,e,w, custom_filter = filter, simplify=False, retain_all=True)
    return G

def get_geometries(city, tags):
    G = ox.geometries.geometries_from_place(city, tags)
    return G

def analyze_sidewalk_data(G, gdf_pois, gdf_bldgs, G_roads):

    gdf = gnx.graph_edges_to_gdf(G)

    gdf['versions'] = None
    gdf['direct_confirmations'] = None
    gdf['changes_to_tags'] = None
    gdf['rollbacks'] = None
    gdf['tags'] = None
    gdf['user_count'] = None
    gdf['days_since_last_edit'] = None


    df_dask = dask_geopandas.from_geopandas(gdf, npartitions=30)  

    df_dask2 = df_dask[["u","v","osmid","geometry", 
                            "versions", "direct_confirmations", "changes_to_tags", "rollbacks", "tags", "user_count",
                            "days_since_last_edit"]]
    output = df_dask2.apply(get_edge_statistics, axis=1, meta=[
        ('u','int64'),
        ('v','int64'),
        ('osmid','int64'),
        ('geometry','geometry'),
        ('versions','object'),
        ('direct_confirmations', 'object'), 
        ('changes_to_tags', 'object'),
        ('rollbacks', 'object'),
        ('tags', 'object'),
        ('user_count', 'object'),
        ('days_since_last_edit', 'object'),
        ]).compute(scheduler='multiprocessing')
        
    G_trust = get_trust(output, gdf_pois, gdf_bldgs, G_roads)


    return G_trust

        

def get_edge_statistics( feature ):
    historical_edge_information = filter_history_by_date(get_item_history_from_id(feature['osmid']))
    edge_stats = calculate_edge_stats(historical_edge_information)
    feature.versions = edge_stats['versions']
    feature.direct_confirmations = edge_stats['direct_confirmations']
    feature.changes_to_tags = edge_stats['changes_to_tags']
    feature.rollbacks = edge_stats['rollbacks']
    feature.user_count = edge_stats['user_count']
    feature.days_since_last_edit = edge_stats['days_since_last_edit']
    feature.tags = edge_stats['tags']
    return feature

def get_feature_statistics( feature ):
    historical_edge_information = filter_history_by_date(get_item_history_from_id(feature['osmid']))
    user_count, days_since_last_edit = calculate_feature_stats(historical_edge_information)
    feature.user_count = user_count
    feature.days_since_last_edit = days_since_last_edit

def filter_history_by_date(historical_edge_information):
    output = {}
    for key,value in historical_edge_information.items():
        if value['timestamp'] <= DATE:
            output[key] = value
    return output



def calculate_edge_stats(historical_edge_information):
    versions = len(historical_edge_information)
    direct_confirmations = calculate_direct_confirmations(historical_edge_information, versions)
    changes_to_tags = calculate_changes_to_tags(historical_edge_information)
    rollbacks = check_rollback(historical_edge_information)
    user_count, days_since_last_edit = calculate_feature_stats(historical_edge_information)
    tags = get_tag_count(historical_edge_information)
    

    return {
        "versions": versions,
        "direct_confirmations": direct_confirmations,
        "changes_to_tags": changes_to_tags,
        "rollbacks": rollbacks,
        "tags": tags,
        "user_count": user_count,
        "days_since_last_edit": days_since_last_edit
    }


def calculate_feature_stats(historical_feature_information):
    user_count = calculate_number_users_edited(historical_feature_information)
    days_since_last_edit = calculate_days_since_last_edit(historical_feature_information)
    return user_count, days_since_last_edit
    
def calculate_days_since_last_edit(historical_feature_information):
    sorted_keys = sorted(historical_feature_information, reverse=True)
    current_edge = historical_feature_information[sorted_keys.pop(0)]
    last_edit_date = current_edge['timestamp']
    diff = DATE - last_edit_date
    return diff.days



def calculate_direct_confirmations(historical_edge_information, len):
    sorted_keys = sorted(historical_edge_information, reverse=True)
    current_edge = historical_edge_information[sorted_keys.pop(0)]
    current_edge_tags = get_relevant_tags(current_edge)

    for key in sorted_keys:
        last_edge = historical_edge_information[key]
        if last_edge['user'] != current_edge['user'] and get_relevant_tags(last_edge) == current_edge_tags:
            return 1
    return 0


def calculate_number_users_edited(historical_edge_information):
    user_list = []
    for edge in historical_edge_information.values():
        if edge['user'] not in user_list:
            user_list.append(edge['user'])
    return len(user_list)

def calculate_changes_to_tags(historical_edge_information):
    change_count = 0
    sorted_keys = sorted(historical_edge_information)

    for i in range(len(sorted_keys)-1):
        tags_1 = get_relevant_tags(historical_edge_information[sorted_keys[i+1]])
        tags_2 = get_relevant_tags(historical_edge_information[sorted_keys[i]])
        for key, value in tags_1.items():
            if tags_2[key] != value:
                change_count += 1
        
    return change_count

def check_rollback(historical_edge_information):
    for edge in historical_edge_information.values():
        if edge['visible'] == False:
            return 1

    return 0


def get_relevant_tags(edge):
    output = {
        'nd': None,
        'footway': None,
        'highway': None,
        'surface': None,
        'crossing': None,
        'lit': None,
        'width': None,
        'tactile_paving': None,
        'access': None,
        'step_count': None
    }
    output['nd'] = edge.get('nd')
    tags = edge.get('tag')
    if tags:
        output['footway'] = tags.get('footway')
        output['highway'] = tags.get('highway')
        output['surface'] = tags.get('surface')
        output['crossing'] = tags.get('crossing')
        output['lit'] = tags.get('lit')
        output['width'] = tags.get('width')
        output['tactile_paving'] = tags.get('tactile_paving')
        output['access'] = tags.get('access')
        output['step_count'] = tags.get('step_count')
    
    return output

def get_tag_count(historical_edge_information):
    tag_count = 0
    sorted_keys = sorted(historical_edge_information, reverse=True)
    current_edge = historical_edge_information[sorted_keys.pop(0)]
    tags = get_relevant_tags(current_edge)
    for key, value in tags.items():
        if value != None:
            tag_count += 1
    return tag_count

def get_trust(G_sidewalk_with_measures, gdf_pois, gdf_bldgs, G_roads):
    G_sidewalk_with_measures = calculate_total_trust_score(G_sidewalk_with_measures, gdf_pois, gdf_bldgs, G_roads)
    return G_sidewalk_with_measures


def calculate_total_trust_score(gdf, gdf_pois, gdf_bldgs, G_roads):

    # calculations for indirect trust
    
    gdf_pois_reset = gdf_pois.reset_index()
    gdf_bldgs_reset = gdf_bldgs.reset_index()
    G_roads_reset = G_roads.reset_index(drop=True)

    G_buffer = get_buffer(gdf)
    G_buffer_reset = G_buffer.reset_index()
    G_poi = get_pois_in_buffer(G_buffer_reset, gdf_pois_reset)
    G_road = get_roads_in_buffer(G_buffer_reset, G_roads_reset) 
    G_bldg = get_bldgs_in_buffer(G_buffer_reset, gdf_bldgs_reset) 

    poi_count_threshold = G_poi['osmid_right'].mean()
    poi_users_threshold = G_poi['user_count'].mean()
    poi_time_threshold = G_poi['days_since_last_edit'].mean()

    road_count_threshold = G_road['osmid_right'].mean()
    road_users_threshold = G_road['user_count'].mean()
    road_time_threshold = G_road['days_since_last_edit'].mean()

    bldg_count_threshold = G_bldg['osmid_right'].mean()
    bldg_users_threshold = G_bldg['user_count'].mean()
    bldg_time_threshold = G_bldg['days_since_last_edit'].mean()

    G_bldg = G_bldg.rename(columns={'osmid_right': 'bldg_count', 'user_count': 'bldg_user_count', 'days_since_last_edit': 'bldg_days_since_last_edit'})
    G_poi = G_poi.rename(columns={'osmid_right': 'poi_count', 'user_count': 'poi_user_count', 'days_since_last_edit': 'poi_days_since_last_edit'})
    G_road = G_road.rename(columns={'osmid_right': 'road_count', 'user_count': 'road_user_count', 'days_since_last_edit': 'road_days_since_last_edit'})

    
    gdf_dask = dask_geopandas.from_geopandas(gdf, npartitions=30)
    gdf_dask = gdf_dask.merge(G_poi, left_on="osmid", right_on="osmid_left")
    gdf_dask = gdf_dask.merge(G_bldg, left_on="osmid", right_on="osmid_left")
    gdf_dask = gdf_dask.merge(G_road, left_on="osmid", right_on="osmid_left")
    # calculations for direct trust
    versions_threshold = gdf_dask['versions'].mean()
    direct_confirm_threshold = gdf_dask['direct_confirmations'].mean()
    changes_to_tags_threshold = 2
    rollbacks_threshold = 1
    tags_threshold = gdf_dask['tags'].mean()
    user_count_threshold = gdf_dask['user_count'].mean()
    
    gdf_dask['direct_trust_score'] = None
    gdf_dask['indirect_trust_score'] = None
    gdf_dask['time_trust_score'] = None
    gdf_dask['trust_score'] = None
 
    # calculations for time trust
    days_since_last_edit_threshold = gdf_dask['days_since_last_edit'].mean()

    if __name__ == '__main__':
        output = gdf_dask.apply(trust_score_calc, 
                           args = (versions_threshold,
                                   direct_confirm_threshold,
                                   changes_to_tags_threshold,
                                   rollbacks_threshold,
                                   tags_threshold,
                                   user_count_threshold,
                                   days_since_last_edit_threshold,
                                   poi_count_threshold,
                                   poi_users_threshold,
                                   poi_time_threshold,
                                   road_count_threshold,
                                   road_users_threshold,
                                   road_time_threshold,
                                   bldg_count_threshold,
                                   bldg_users_threshold,
                                   bldg_time_threshold
                                   ), 
                           axis=1,
                           meta=[
        ('u','int64'),
        ('v','int64'),
        ('osmid','int64'),
        ('geometry','geometry'),
        ('versions','object'),
        ('direct_confirmations', 'object'), 
        ('changes_to_tags', 'object'),
        ('rollbacks', 'object'),
        ('tags', 'object'),
        ('user_count', 'object'),
        ('days_since_last_edit', 'object'),
        ('poi_count', 'object'),
        ('poi_user_count', 'object'),
        ('poi_days_since_last_edit', 'object'),
        ('bldg_count', 'object'),
        ('bldg_user_count', 'object'),
        ('bldg_days_since_last_edit', 'object'),
        ('road_count', 'object'),
        ('road_user_count', 'object'),
        ('road_days_since_last_edit', 'object'),
        ('direct_trust_score', 'object'),
        ('indirect_trust_score', 'object'),
        ('time_trust_score', 'object'),
        ('trust_score', 'object')
        ]).compute(scheduler='multiprocessing')

        return output
    else:
        print("direct trust calc failed")
        return gdf_dask

def trust_score_calc(feature, versions_threshold, direct_confirm_threshold, changes_to_tags_threshold, 
                            rollbacks_threshold, tags_threshold, user_count_threshold, days_since_last_edit_threshold,  
                            poi_count_threshold, poi_users_threshold, poi_time_threshold, road_count_threshold, road_users_threshold,
                            road_time_threshold, bldg_count_threshold, bldg_users_threshold, bldg_time_threshold):
    
    indirect_trust_score = 0
    if feature['road_count'] >= road_count_threshold:
        indirect_trust_score += 1
    if feature['road_user_count'] >= road_users_threshold:
        indirect_trust_score +=1
    if feature['road_days_since_last_edit'] >= road_time_threshold:
        indirect_trust_score += 1
    try:
        if feature['poi_count'] >= poi_count_threshold:
            indirect_trust_score +=1
    except KeyError:
        print("error")
    if feature['poi_user_count'] >= poi_users_threshold:
        indirect_trust_score += 1
    if feature['poi_days_since_last_edit'] >= poi_time_threshold:
        indirect_trust_score += 1
    if feature['bldg_count'] >= bldg_count_threshold:
        indirect_trust_score +=1
    if feature['bldg_user_count'] >= bldg_users_threshold:
        indirect_trust_score += 1
    if feature['bldg_days_since_last_edit'] >= bldg_time_threshold:
        indirect_trust_score += 1
        
    feature.indirect_trust_score = int(indirect_trust_score > 2)

    
    direct_trust_score = 0
    if feature['versions'] >= versions_threshold:
        direct_trust_score += .2
    if feature['direct_confirmations'] >= direct_confirm_threshold:
        direct_trust_score +=.2
    if feature['user_count'] >= user_count_threshold:
        direct_trust_score += .2
    if feature['rollbacks'] >= rollbacks_threshold:
        direct_trust_score +=.1
    if feature['changes_to_tags'] >= changes_to_tags_threshold:
        direct_trust_score += .1
    if feature['tags'] >= tags_threshold:
        direct_trust_score += .2
    feature.direct_trust_score = direct_trust_score

    feature.time_trust_score = int(feature['days_since_last_edit'] > days_since_last_edit_threshold)
    feature.trust_score = (feature.direct_trust_score*.5) + (feature.indirect_trust_score*.25) + (feature.time_trust_score*.25)

    return feature


def get_buffer(G):

    G = G.to_crs({'init': PROJ})
    G['geometry'] = G.geometry.buffer(1000)

    return G

def get_pois_in_buffer(G_buffer, gdf_pois):

    buffer_with_pois = dask_geopandas.GeoDataFrame.sjoin(G_buffer, gdf_pois, how='inner', predicate='intersects')
    buffer_with_pois = buffer_with_pois.groupby('osmid_left').agg( 
        {'osmid_right':'count', 
         'user_count': 'sum', 
         'days_since_last_edit': 'sum'}) 
    
    return buffer_with_pois

def get_bldgs_in_buffer(G_buffer, gdf_bldgs):
    buffer_with_bldgs = dask_geopandas.GeoDataFrame.sjoin(G_buffer, gdf_bldgs, how='inner', predicate='intersects')
    buffer_with_bldgs = buffer_with_bldgs.groupby('osmid_left').agg(
        {'osmid_right':'count', 
         'user_count': 'sum', 
         'days_since_last_edit': 'sum'}) 
    
    return buffer_with_bldgs

def get_roads_in_buffer(G_buffer, gdf_roads):

    buffer_with_roads = dask_geopandas.GeoDataFrame.sjoin(G_buffer, gdf_roads, how='inner', predicate='intersects')
    buffer_with_roads = buffer_with_roads.groupby('osmid_left').agg(
        {'osmid_right':'count',
         'user_count': 'sum', 
         'days_since_last_edit': 'sum'})
    
    return buffer_with_roads









#main_bbox(47.71, 47.65, -122.06, -122.18) #redmond original  47.71, 47.65, -122.06, -122.18
main_bbox(47.7139,47.6977,-122.1106,-122.1391) #redmond testing subset


#main_bbox(47.6553, 47.6469, -122.3377, -122.3613) #, "C:\\Users\\jessica\\Documents\\ArcGIS\\Projects\\SeattleIndexing\\Fremont Tiling.geojson")
#main("Gustavus, AK, USA")
#main("Mount Vernon, Skagit County, Washington, 98273, United States")
#main_bbox(48.42342, 48.42002, -122.32707, -122.33572)

#main(47.6371, 47.6182, -122.3219, -122.3532)
