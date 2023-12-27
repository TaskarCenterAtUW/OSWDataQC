import pandas as pd
import os

STATS_BY_NBHOOD = {}

def calculate(filepath, date):
    centralities_df = pd.read_csv(filepath)
    stats_by_nbhood = get_stats_by_nbhood(centralities_df)
    centralities_df_with_variance = get_variances(centralities_df, stats_by_nbhood)
    print(centralities_df_with_variance)
    centralities_df_with_variance.to_csv(os.path.join("C:\\Users\\jessb\\Documents\\wokr\\redmond", ('redmond_centralities_with_variance_' + date + '.csv')))


def get_stats_by_nbhood(centralities_df):
    stats_by_nbhood = centralities_df.groupby('NAME')\
        .agg({'betweennes':['mean', 'std'], 
              'degree': ['mean', 'std'],
              'eigen':['mean', 'std'],
              'bet_stdev':['mean', 'std'],
              'trust_scor':['mean', 'std'],
              'direct_tru':['mean', 'std']})
    #change later but this works for now
    global STATS_BY_NBHOOD 
    STATS_BY_NBHOOD = stats_by_nbhood.to_dict()
    print(STATS_BY_NBHOOD)
    return stats_by_nbhood

def get_variances(centralities_df, stats_by_nbhood):
    centralities_df['v_betweenness'] = centralities_df.apply(get_variance, args = ('betweennes',), axis = 1)
    centralities_df['v_eigen'] = centralities_df.apply(get_variance, args = ('eigen',), axis = 1)
    centralities_df['v_degree'] = centralities_df.apply(get_variance, args = ('degree',), axis = 1)
    centralities_df['v_direct_tru'] = centralities_df.apply(get_variance, args = ('direct_tru',), axis = 1)
    centralities_df['v_trust_scor'] = centralities_df.apply(get_variance, args = ('trust_scor',), axis = 1)
    return centralities_df

def get_variance(row, value):
    return check_variance(row[value], STATS_BY_NBHOOD[(value, 'mean')][row['NAME']], STATS_BY_NBHOOD[(value, 'std')][row['NAME']])
    

def check_variance(value, mean, sd):
    if value == mean:
        return 0
    elif value < mean:
        if value > mean - sd:
            return -1
        else:
            return -2
    else:
        if value < mean + sd:
            return 1
        else:
            return 2
        
calculate("C:\\Users\\jessb\\Documents\\wokr\\redmond\\tasks_with_nbhoods_dec_12.csv", "dec_12")
calculate("C:\\Users\\jessb\\Documents\\wokr\\redmond\\tasks_with_nbhoods_oct_17.csv", "oct_17")
calculate("C:\\Users\\jessb\\Documents\\wokr\\redmond\\tasks_with_nbhoods_sept_8.csv", "sept_8")
calculate("C:\\Users\\jessb\\Documents\\wokr\\redmond\\tasks_with_nbhoods_sept_21.csv", "sept_21")
calculate("C:\\Users\\jessb\\Documents\\wokr\\redmond\\tasks_with_nbhoods_july_1.csv", "july_1")