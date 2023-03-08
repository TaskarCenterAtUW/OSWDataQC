from util.osm_bb_data import get_map_data


small_bb = [-122.34801,47.64884,-122.34750, 47.64900]
med_bb = [ -122.34972, 47.64927,-122.34738, 47.64952]
big_bb = [-122.34976, 47.64825, -122.34738, 47.64971]
def main(bb):
    map_data = get_map_data(bb)
    network_data = []
    for element in map_data:
        if element['type'] == 'way' and 'highway' in element['data']['tag']:
            new_element = {'id': element['data']['id'], 'tag': element['data']['tag'], 'nd': element['data']['nd'] }
            network_data.append(new_element)

    print(network_data)

main(med_bb)