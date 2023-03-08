from osmapi import OsmApi
import requests

USERNAME = ""
PASSWORD = ""
OSMAPICONNECTION = OsmApi(username = USERNAME, password = PASSWORD)
URL = "https://api.openstreetmap.org/api/0.6/"

def get_map_data(bounding_params):
    '''Uses the OSM API to get all data within a bounding box as defined by min/max long and lat.'''

    map_data = OSMAPICONNECTION.Map(min_lon=bounding_params[0],min_lat=bounding_params[1],max_lon=bounding_params[2],max_lat=bounding_params[3])
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
    elif item_type == 'way':python
        history = OSMAPICONNECTION.WayHistory(id)
    elif item_type == 'relation':
        history = OSMAPICONNECTION.RelationHistory(id)
    
    return history

def get_item_user_history(item):
    user_id = item["data"]["uid"]
    request_url = URL + f"changesets?user={user_id}"
    response = requests.get(request_url)

    if response.status_code == 200:
        changeset_xml = response.text
        print("user history: \n\n")
        print(changeset_xml)
    else:
        print("Error retrieving changeset information")

def get_way_details(item):
    id = item["data"]["id"]
    request_url = URL + f"way/{id}/full"
    response = requests.get(request_url)

    if response.status_code == 200:
        changeset_xml = response.text
        print("way info: \n\n")
        print(changeset_xml)
    else:
        print("Error retrieving changeset information")
    

def get_way_details_further(item):
    id = item["data"]["id"]
    request_url = URL + f"ways?ways={id}v1"
    response = requests.get(request_url)

    if response.status_code == 200:
        changeset_xml = response.text
        print("way info: \n\n")
        print(changeset_xml)
    else:
        print("Error retrieving changeset information")
    



