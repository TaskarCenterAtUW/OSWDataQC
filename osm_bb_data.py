from osmapi import OsmApi

USERNAME = ""
PASSWORD = ""
OSMAPICONNECTION = OsmApi(username = USERNAME, password = PASSWORD)

def get_map_data(min_lon, min_lat, max_lon, max_lat):
    '''Uses the OSM API to get all data within a bounding box as defined by min/max long and lat.'''

    map_data = OSMAPICONNECTION.Map(min_lon=min_lon,min_lat=min_lat,max_lon=max_lon,max_lat=max_lat)
    return map_data

def get_changeset_by_id(changeset_id):
    '''Uses the OSM API to get the changeset information using changeset ID.'''

    changeset_json = OSMAPICONNECTION.ChangesetGet(changeset_id)
    return changeset_json

def get_item_history(item):
    '''Uses the OSM API to get the item history for any given node, way, or relation object.'''
    
    history = {}
    item_type = item['type']
    id = item['data']['id']

    if item_type == 'node':
        history = OSMAPICONNECTION.NodeHistory(id)
    elif item_type == 'way':
        history = OSMAPICONNECTION.WayHistory(id)
    elif item_type == 'relation':
        history = OSMAPICONNECTION.RelationHistory(id)
    
    return history
    

def main():
    '''Gets all items within a bounding box and prints the history and most recent changeset info for the first item.'''

    map_data = get_map_data(-122.34801,47.64884,-122.34750,47.64900)
    item = map_data[0]

    sample_history = get_item_history(item)
    sample_changeset = get_changeset_by_id(item['data']['changeset'])

    print(f'''Item: {item}''')
    print(f'''History: {sample_history}''')
    print(f'''Changeset: {sample_changeset}''')

main()
