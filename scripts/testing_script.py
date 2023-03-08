from util.osm_bb_data import get_map_data, get_item_history, get_changeset_by_id, get_item_user_history, get_way_details, get_way_details_further

def main():
    '''Gets all items within a bounding box and prints the history and most recent changeset info for the first item.'''

    map_data = get_map_data(-122.34801,47.64884,-122.34750,47.64900)
    for element in map_data:
        if element['type'] == 'way':
            item = element
            break

    sample_history = get_item_history(item)
    sample_changeset = get_changeset_by_id(item['data']['changeset'])

    print(f'''Item: {item}''')
    print(f'''History: {sample_history}''')
    print(f'''Changeset: {sample_changeset}''')

    get_item_user_history(item)
    get_way_details(item)
    get_way_details_further(item)

main()