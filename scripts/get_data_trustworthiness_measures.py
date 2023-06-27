import osmnx as ox
from util.osm_bb_data import get_item_history_from_id


# pull ped network for city of seattle
def get_network(city):
    G = ox.graph.graph_from_place(city, custom_filter = '["highway"~"footway"]', simplify=False, retain_all=True)
    return G
    
# go through each sidewalk edge and analyze the criteria
def filter_sidewalk_edges(G):
    output = {}
    for edge in G.edges():
        for n, nbrsdict in G.adjacency():
            for nbr, keydict in nbrsdict.items():
                for key, eattr in keydict.items():
                    if eattr['highway'] == 'footway':
                        historical_edge_information = get_item_history_from_id(eattr['osmid'])
                        scores = calculate_trust_metrics(historical_edge_information, eattr)
                        output[eattr['osmid']] = scores

def calculate_trust_metrics(historical_edge_information, current_edge_information):                      
        direct = calculate_direct(historical_edge_information)
        indirect = calculate_indirect(historical_edge_information, current_edge_information)
        time = calculate_time(historical_edge_information)
        trust_score = calculate_trust_score(direct, indirect, time)

        {
            "edge": current_edge_information,
            "direct_indicator": direct,
            "indirect_indicator": indirect,
            "time_indicator": time,
            "trust_score": trust_score
        }

        return

def calculate_direct(historical_edge_information):
    versions_weight = .2
    direct_confirmations_weight = .2
    threshhold_user_count = 3 #todo: this needs to be determined by city median
    user_count_weight = .2
    threshhold_changes_to_tag = 2
    changes_to_tags_weight = .1
    rollback_weight = .1
    threshold_tags = 2 #todo this should be median
    tags_weight = .2

    versions = len(historical_edge_information) * versions_weight
    direct_confirmations = calculate_direct_confirmations(historical_edge_information) * direct_confirmations_weight
    user_count = (calculate_number_users_edited(historical_edge_information) >= threshhold_user_count) * user_count_weight
    changes_to_tags = (calculate_changes_to_tags(historical_edge_information) >= threshhold_changes_to_tag) * changes_to_tags_weight
    rollbacks = check_rollback(historical_edge_information) * rollback_weight
    tags = (get_tag_count(historical_edge_information) >= threshold_tags) * tags_weight
    
    direct_indicator = versions + direct_confirmations + user_count + changes_to_tags + rollbacks + tags

    return direct_indicator

def calculate_direct_confirmations(historical_edge_information):
    count = len(historical_edge_information)
    current_edge = historical_edge_information[count]

    # make sure we're looking at different users
    while last_edge['user'] == current_edge['user']:
        count -= 1
        last_edge = historical_edge_information[count]

    return get_relevant_tags(last_edge) == get_relevant_tags(current_edge)

def calculate_number_users_edited(historical_edge_information):
    user_list = []
    for edge in historical_edge_information.values():
        if edge['user'] not in user_list:
            user_list.append(edge['user'])
    return len(user_list)

def calculate_changes_to_tags(historical_edge_information):
    change_count = 0
    edge_count = len(historical_edge_information)
    while edge_count > 0:
        tags_1 = get_relevant_tags(historical_edge_information[edge_count])
        edge_count -= 1
        tags_2 = get_relevant_tags(historical_edge_information[edge_count])
        for key, value in tags_1.items():
            if tags_2[key] != value:
                change_count += 1
    return change_count

def check_rollback(historical_edge_information):
    edge_count = len(historical_edge_information)
    #TODO: need to find an example of how this looks
    return 1


def get_relevant_tags(historical_edge_information):
    output = []
    output['nd'] = historical_edge_information.get('nd')
    output['footway'] = historical_edge_information['tag'].get('footway')
    output['highway'] = historical_edge_information['tag'].get('highway')
    output['surface'] = historical_edge_information['tag'].get('surface')
    output['crossing'] = historical_edge_information['tag'].get('crossing')

def get_tag_count(historical_edge_information):
    tag_count = 0
    tags = get_relevant_tags(historical_edge_information)
    for key, value in tags.items():
        if value != None and key != 'crossing':
            tag_count += 1
    return tag_count

def calculate_indirect(edge, attributes):
    # grab osm data for 1 sq km area from edge
    # 
    return

def calculate_time(edge):
    return

def calculate_trust_score(direct, indirect, time):
    return

# turn this into a csv with all measures calculated


# to get the measures of central tendency, analysis will be run over this entire dataset
# based on these measures, go through each edge and calculate a trustworthiness score
# save this to a csv



# once this is done, this will get connected back to the network testing script
# in this script, each tile will use the edge id as a pk to pull the trustworthiness scores
# the scores will then be averaged and applied to the entire tile







def main(city):
    G = get_network(city)
    filter_sidewalk_edges(G)

main("Bellevue, Washington, USA")
