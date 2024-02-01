
# recd g from csv file
special_keys = {'msgSender','now'}


if __name__ == '__main__':
    from pprint import pprint
    import pandas as pd
    import networkx as nx
    import os
    import json
    import matplotlib.pyplot as plt
    import csv
    from algo import get_minimal_all,set_of_minimal_relations

    from utils import traceback_upstream_dag, plot_graph, node_label

    # for root, dirs, files in os.walk("/Users/tao/Projects/datalog_graph/declarative-smart-contracts/temp", topdown=False):

    for root, dirs, files in os.walk("./view-materialization/relation-dependencies", topdown=False):
        for name in files:
            name_normalize = str.lower(name.split('.')[0][0])+name.split('.')[0][1:]
            print(name_normalize)
            # if not 'bnb' in name_normalize:
            #     continue 

            datalog_file = os.path.join("./benchmarks", name_normalize.split(".")[0] + '.dl')
            print(os.path.join("./benchmarks", name_normalize.split(".")[0] + '.dl'))
            df = pd.read_csv(os.path.join(root, name),header=0)


            # construct the g
            stored_key_txn = {'send','transfer','call'}
            txn_head_all = set()
            G = nx.DiGraph()
            for i,r in df.iterrows():
                if(r['#body']==' '):
                    if(r['isTx']):
                        txn_head_all.add(r['head'])
                    continue
                edge_data = G.get_edge_data(r['#body'], r['head'])
                if edge_data is None:
                    G.add_edge(r['#body'], r['head'], is_agg= r['isAgg'], rule_id= (r['ruleId'],), is_txn=r['isTx'])
                    if r['isTx'] or (r['head'] in stored_key_txn):
                        txn_head_all.add(r['head'])
                else:
                    assert edge_data['is_agg'] == r['isAgg']
                    edge_data['is_txn'] = edge_data['is_txn']  or r['isTx']
                    edge_data['rule_id'] = tuple(sorted(edge_data['rule_id'] +  (r['ruleId'],) ))
                    print(edge_data['rule_id'])
                    print( r['#body'], r['head'], G.get_edge_data(r['#body'], r['head']) )
            print('\n\n\ntxn_head_all')
            print(txn_head_all)

  
            calculate_on_demand = []
            public_relation_readonly = []
            with open(datalog_file,'r') as dl:
                for l in dl:
                    if '//' in l:
                        continue
                    if '.public' in l and (not 'recv_' in l):
                        public_relation_readonly.append(l.split(' ')[1].split('(')[0])
                    elif '.function' in l:
                        calculate_on_demand.append(l.split(' ')[1].split('\n')[0])
            print('\n\ncalculate on demand')
            pprint(calculate_on_demand)
            print('\n\npublic_relation_readonly')
            pprint(public_relation_readonly)


            # get full set
            full_set = set()
            full_file = os.path.join("./view-materialization/full-set/", name_normalize.split(".")[0] + '.csv')
            print(os.path.join("./view-materialization/full-set/", name_normalize.split(".")[0] + '.csv'))
            with open(full_file, 'r') as full:
                csv_reader = csv.reader(full)
                for row in csv_reader:
                    full_set = full_set.union(set(row))
            print("\nfull set")
            pprint(full_set)



            # direct dependency relations
            full_set.discard('')
            direct_dependency_set_all = full_set




            upstream_dag =  traceback_upstream_dag(direct_dependency_set_all, txn_head=txn_head_all,g=G)
            # plot_graph(G)
            # plot_graph(upstream_dag)

            mms_from_direct_dependency = set_of_minimal_relations(direct_dependency_set_all, direct_dependency_set_all, upstream_dag)
            print('\n\nmms_from_direct_dependency') # Lan: should this be unique? => yes, given proof
            pprint( node_label(mms_from_direct_dependency, upstream_dag))
            minimal_all = get_minimal_all(mms_from_direct_dependency, direct_dependency_set_all, upstream_dag)

            # Lan: remove min-sets with datalog defined functions, and generate func_set
            invalid_min_set = set()
            for min_set in minimal_all:
                if not len(set(min_set) & set(calculate_on_demand)) == 0:
                    invalid_min_set.add(min_set)

            minimal_all = minimal_all - invalid_min_set
            print("count minimal_all", len(minimal_all))
            pprint(node_label(minimal_all,upstream_dag))



            # get min set with its corresponding function set
            min_func_all = list()
            for min_set in minimal_all:
                min_set = set(min_set) - special_keys # remove all special keys
                if "bnb" in name_normalize:
                    min_set.add("freezeOf")
                if "nft" in name_normalize:
                    min_set.add("ownerOf")
                if "tether" in name_normalize:
                    min_set.add("transferFromWithoutFee")
                    min_set.add("transferWithFee")
                func_set = ((full_set - set(min_set)) & direct_dependency_set_all) | set(calculate_on_demand)
                min_func_list = list(min_set)
                min_func_list.extend([""]+list(func_set))
                print("\nmin & function relations")
                pprint(min_func_list)
                min_func_all.append(min_func_list)
            
            with open("./view-materialization/min-noArithmetic/" + name_normalize.split(".")[0] + '.csv', 'w', newline='') as file:
                csv_writer = csv.writer(file)
                for row in min_func_all:
                    csv_writer.writerow(row)


