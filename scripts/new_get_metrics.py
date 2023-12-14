import os
os.environ['USE_PYGEOS'] = '0'
import networkx as nx
import geopandas as gpd
import os
import osmnx as ox
import dask_geopandas
from statistics import stdev, mean
from osmapi import OsmApi
import geonetworkx as gnx
from datetime import datetime
import pandas as pd
from shapely.ops import voronoi_diagram
from shapely import intersection
import logging

DATE = datetime.now() 
PROJ = 'epsg:26910'
SIDEWALK_FILTER = '["highway"~"footway|steps|living_street|path"]'

USERNAME = ""
PASSWORD = ""
OSMAPICONNECTION = OsmApi(username = USERNAME, password = PASSWORD)
URL = "https://api.openstreetmap.org/api/0.6/"

def get_way_history_from_id(osmid):
    return OSMAPICONNECTION.WayHistory(osmid)

def get_map_data(bounding_params):
    '''Uses the OSM API to get all data within a bounding box as defined by min/max long and lat.'''

    map_data = OSMAPICONNECTION.Map(min_lon=bounding_params[0],min_lat=bounding_params[1],max_lon=bounding_params[2],max_lat=bounding_params[3])
    return map_data

def settings_init(settings):
    if 'date' in settings.keys():
        globals()['DATE'] = datetime.strptime(settings['date'], "%Y-%m-%dT%H:%M:%SZ")
    if 'proj' in settings.keys():
        globals()['PROJ'] = settings['proj']


def get_item_history(item):
    '''Uses the OSM API to get the item history for any given node, way, or relation object.'''
    
    history = {}
    if 'element_type' in item:
        item_type = item['element_type']
    else:
        return None
    id = item.get('osmid')

    if item_type == 'node':
        history = OSMAPICONNECTION.NodeHistory(id)
    elif item_type == 'way':
        history = OSMAPICONNECTION.WayHistory(id)
    elif item_type == 'relation':
        history = OSMAPICONNECTION.RelationHistory(id)
    
    return history


def func( feature ):
    poly = feature.geometry
    if (poly.geom_type == "Polygon" or poly.geom_type == "MultiPolygon"):
        measures = get_measures_from_polygon(poly)
        feature.direct_trust_score = measures["direct_trust_score"]
        feature.time_trust_score = measures["time_trust_score"]
        feature.indirect_values = measures["indirect_values"]
        return feature

def analyze_area(filename, path = 'pwd', settings = {}):
    if path == 'pwd':
        path = os.getcwd()
    
    settings_init(settings)

    logging_filename = path + "logs"
    logging.basicConfig(filename=logging_filename,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

    gdf = gpd.read_file(os.path.join(path, (filename + '.geojson')))
    if len(gdf.index) == 1:
        # If tiling isn't present in data, we will create our own tiling
        gdf_roads_simplified = ox.graph.graph_from_polygon(gdf.geometry.loc[0], network_type = 'drive', simplify=True, retain_all=True)
        gdf = create_voronoi_diagram(gdf_roads_simplified, gdf.geometry.loc[0])
 

    gdf['direct_confirmations'] = None
    gdf['direct_trust_score'] = None
    gdf['time_trust_score'] = None
    gdf['indirect_values'] = None

    df_dask = dask_geopandas.from_geopandas(gdf, npartitions=16, name = 'measures')
    

    if __name__ == '__main__':
        output = df_dask.apply(func, axis=1, meta=gpd.GeoDataFrame( {
            'geometry': 'geometry',
            'direct_confirmations': 'object',
            'direct_trust_score': 'object',
            'time_trust_score': 'object',
            'indirect_values': 'object'}
            , index=[0])).compute(scheduler='multiprocessing')

        threshhold_values = get_threshhold_values(output)
        output['indirect_trust_score'] = output.apply(lambda x: indirect_trust_calc(x, threshhold_values), axis=1)
        output['trust_score'] = output.apply(lambda x: trust_calc(x), axis=1)

        total_trust_score = output["trust_score"].mean()

        return total_trust_score

def indirect_trust_calc(feature, threshholds):
    indirect_trust_score = 0
    item_name_array = ['road_time', 'road_users', 'road_time', 'poi_count', 'poi_users', 'poi_time', 'bldg_count', 'bldg_count', 'bldg_users', 'bldg_time']
    for item_name in item_name_array:
        if feature.indirect_values != None and feature.indirect_values[item_name] != None and feature.indirect_values[item_name] >= threshholds[item_name]:
            indirect_trust_score += 1
        
    return int(indirect_trust_score > 2)

def trust_calc(feature):
    return (feature.direct_trust_score*.5) + (feature.indirect_trust_score*.25) + (feature.time_trust_score*.25)

def get_threshhold_values(gdf):
        gdf2 = pd.json_normalize(gdf['indirect_values'])
        threshholds = {
            "poi_count": gdf2['poi_count'].mean(),
            "bldg_count": gdf2['bldg_count'].mean(),
            "road_count": gdf2['road_count'].mean(),
            "poi_users": gdf2['poi_users'].mean(),
            "road_users": gdf2['road_users'].mean(),
            "bldg_users": gdf2['bldg_users'].mean(),
            "poi_time": gdf2['poi_time'].mean(),
            "road_time": gdf2['road_time'].mean(),
            "bldg_time": gdf2['bldg_time'].mean(),
        }
        return threshholds
    
def get_measures_from_polygon(polygon):
    try:
        G = ox.graph.graph_from_polygon(polygon, custom_filter = SIDEWALK_FILTER, truncate_by_edge=True, simplify=False, retain_all=True)
    except ValueError as e:
        logging.warning(f"Unexpected {e}, {type(e)} with polygon {polygon} when getting graph")
        return {"direct_trust_score": None, "time_trust_score": None, "indirect_values": None}
    #stats = get_centrality(G, polygon)
    stats = {}
    direct_trust_score, time_trust_score = analyze_sidewalk_data(G)

    stats["direct_trust_score"] = direct_trust_score
    stats["time_trust_score"] = time_trust_score

    stats['indirect_values'] = get_indirect_trust_score_from_polygon(polygon)



    
    return stats

def get_indirect_trust_score_from_polygon(polygon):
    try:
        gdf_pois = ox.features.features_from_polygon(polygon, tags = {'amenity': True}).to_crs({'init': PROJ})
    except ValueError as e:
        logging.warning(f"Unexpected {e}, {type(e)} with polygon {polygon} when getting graph")
        gdf_pois = gpd.GeoDataFrame(columns=['amenity', 'operator', 'nodes', 'geometry'], geometry='geometry')
    try:
        gdf_bldgs = ox.features.features_from_polygon(polygon, tags = {'building': True}).to_crs({'init': PROJ})
    except ValueError as e:
        logging.warning(f"Unexpected {e}, {type(e)} with polygon {polygon} when getting graph")
        gdf_bldgs = gpd.GeoDataFrame(columns=['geometry', 'amenity', 'nodes'], geometry='geometry')
    try:
        G_roads = ox.graph.graph_from_polygon(polygon, network_type = 'drive', simplify=False, retain_all=True)
        gdf_roads = gnx.graph_edges_to_gdf(G_roads).to_crs({'init': PROJ})
    except ValueError as e:
        logging.warning(f"Unexpected {e}, {type(e)} with polygon {polygon} when getting graph")
        gdf_roads = gpd.GeoDataFrame(columns=['u', 'v', 'osmid', 'highway', 'reversed', 'length', 'geometry', 'lanes', 'name', 'maxspeed', 'bridge', 'ref'], geometry='geometry') 
    
    values_dict = {
        "poi_count": len(gdf_pois.index),
        "bldg_count": len(gdf_bldgs.index),
        "road_count": len(gdf_roads.index),
        "poi_users": None,
        "road_users": None,
        "bldg_users": None,
        "poi_time": None,
        "road_time": None,
        "bldg_time": None,
    }
    values_dict["poi_users"], values_dict["poi_time"] = filter_through_items_for_stats(gdf_pois)
    values_dict["road_users"], values_dict["road_time"] = filter_through_items_for_stats(gdf_roads)
    values_dict["bldg_users"], values_dict["bldg_time"] = filter_through_items_for_stats(gdf_bldgs)

    return values_dict

def filter_through_items_for_stats(gdf):
    user_count_array = []
    days_since_last_edit_array = []
    mean_user_count_array = 0
    mean_days_since_last_edit_array = 0
    for index, row in gdf.iterrows(): 
        historical_information = get_item_history(row)
        if not historical_information:
            user_count, days_since_last_edit = 0, None
        else:
            user_count, days_since_last_edit = calculate_feature_stats(historical_information)
        user_count_array.append(user_count)
        days_since_last_edit_array.append(days_since_last_edit)
    if user_count_array and len(user_count_array) != 0:
        mean_user_count_array = mean(user_count_array)
    if days_since_last_edit_array and len(days_since_last_edit_array) != 0:
        try:
            mean_days_since_last_edit_array = mean(days_since_last_edit_array)
        except TypeError as e:
            mean_days_since_last_edit_array = None
    return mean_user_count_array, mean_days_since_last_edit_array



def get_centrality(G, polygon):
    stats = {}
    undirected_g = nx.Graph(G)

    bet = nx.betweenness_centrality(undirected_g, normalized = True, endpoints=False)
    try:
        eigen = nx.eigenvector_centrality(undirected_g, max_iter=1000)
        stats["eig_centrality_avg"] = mean(eigen.values())
    except Exception as e:
        logging.warning(f"Unexpected {e}, {type(e)} with polygon {polygon} when getting eigen value")
        stats["eig_centrality_avg"] = None

    deg = nx.degree_centrality(undirected_g)
    stats["bet_centrality_avg"] = mean(bet.values())
    stats["deg_centrality_avg"] = mean(deg.values())
    stats["bet_stdev"] = stdev(bet.values())
    return stats

def analyze_sidewalk_data(G):

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
        
    direct_trust_score, time_trust_score = calculate_total_trust_score(output)


    return direct_trust_score, time_trust_score

def get_edge_statistics( feature ):
    historical_edge_information = filter_history_by_date(get_way_history_from_id(feature['osmid']))
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
    historical_edge_information = filter_history_by_date(get_way_history_from_id(feature['osmid']))
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



def calculate_total_trust_score(gdf):
    gdf_dask = dask_geopandas.from_geopandas(gdf, npartitions=30)
    # calculations for direct trust
    versions_threshold = gdf_dask['versions'].mean()
    direct_confirm_threshold = gdf_dask['direct_confirmations'].mean()
    changes_to_tags_threshold = 2
    rollbacks_threshold = 1
    tags_threshold = gdf_dask['tags'].mean()
    user_count_threshold = gdf_dask['user_count'].mean()
    
    gdf_dask['direct_trust_score'] = None
    gdf_dask['time_trust_score'] = None
 
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
        ('direct_trust_score', 'object'),
        ('time_trust_score', 'object')
        ]).compute(scheduler='multiprocessing')

        direct_trust_score = output['direct_trust_score'].mean()
        time_trust_score = output['time_trust_score'].mean()
        return direct_trust_score, time_trust_score
    else:
        logging.error("direct trust calc failed")
        return 0

def trust_score_calc(feature, versions_threshold, direct_confirm_threshold, changes_to_tags_threshold, 
                            rollbacks_threshold, tags_threshold, user_count_threshold, days_since_last_edit_threshold):

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

    return feature

def create_voronoi_diagram(G_roads_simplified, bounds):
    # first thin the nodes 
    gdf_roads_simplified = gnx.graph_edges_to_gdf(G_roads_simplified)
    voronoi = voronoi_diagram(gdf_roads_simplified.boundary.unary_union, envelope = bounds)
    voronoi_gdf = gpd.GeoDataFrame({"geometry": voronoi.geoms})
    voronoi_gdf.set_crs(PROJ)
    voronoi_gdf_clipped = gpd.clip(voronoi_gdf, bounds)
    
    return voronoi_gdf_clipped



analyze_area("redmond_town_center", "C:\\Users\\jessb\\Downloads")
