
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
            #print('\n\n\n\n read csv file ' + name)
            #print(os.path.join(root, name))
            name_normalize = str.lower(name.split('.')[0][0])+name.split('.')[0][1:]
            print(name_normalize)
            # if not 'auction' in name_normalize:
            #     continue 

            datalog_file = os.path.join("./benchmarks", name_normalize.split(".")[0] + '.dl')
            print(os.path.join("./benchmarks", name_normalize.split(".")[0] + '.dl'))
            
            public_relation_readonly = []
            calculate_on_demand = []
            with open(datalog_file,'r') as dl:
                for l in dl:
                    if '//' in l:
                        continue
                    if '.public' in l and (not 'recv_' in l):
                        public_relation_readonly.append(l.split(' ')[1].split('(')[0])
                        # print('public', public_relation_readonly[-1])
                    elif '.function' in l:
                        calculate_on_demand.append(l.split(' ')[1])
            print('\n\npublic_relation_readonly') # may include some relations from calculate_on_demand => remove such min-set choices
            pprint(public_relation_readonly)
            print('\n\ncalculate on demand') # relationshave three types: txn, materialize, calculate on demand(func_set)
            pprint(calculate_on_demand)
            df = pd.read_csv(os.path.join(root, name),header=0)


            # construct the g
            stored_key_txn = {'send','transfer','call'}
            txn_head_all = set()
            G = nx.DiGraph()
            for i,r in df.iterrows():
                # G.add_edge(r['#body'], r['head'], is_agg= r['isAgg'], rule_id= r['ruleId'],)
                edge_data = G.get_edge_data(r['#body'], r['head'])
                if edge_data is None:
                    G.add_edge(r['#body'], r['head'], is_agg= r['isAgg'], rule_id= (r['ruleId'],), is_txn=r['isTx'])
                    if r['isTx'] or (r['head'] in stored_key_txn):
                        txn_head_all.add(r['head'])
                else:
                    assert edge_data['is_agg'] == r['isAgg']
                    # assert edge_data['is_txn'] == r['isTx']
                    edge_data['is_txn'] = edge_data['is_txn']  or r['isTx']
                    edge_data['rule_id'] = tuple(sorted(edge_data['rule_id'] +  (r['ruleId'],) ))
                    print(edge_data['rule_id'])
                    print( r['#body'], r['head'], G.get_edge_data(r['#body'], r['head']) )

            print('\n\n\ntxn_head_all')
            print(txn_head_all)



            # direct dependency relations
            direct_dependency_set_all = set() # may also include some relations from calculate_on_demand => remove such min-set choices
            for thead in txn_head_all:
                for pred in G.predecessors(thead):
                    print(pred)
                    # well-defined datalog
                    if ((thead in txn_head_all) or (thead in calculate_on_demand)):
                        if not (pred in txn_head_all or pred.startswith('recv_') or pred in calculate_on_demand):
                            direct_dependency_set_all.add(pred)
            direct_dependency_set_all = direct_dependency_set_all - special_keys # Lan: remove special keys
            print('\n\n\ndirect_dependency_set_all')
            pprint(direct_dependency_set_all)
            # pos = nx.nx_agraph.graphviz_layout(G, prog='neato')
            #
            # nx.draw(G, pos, with_labels=True, font_weight='normal')
            # plt.show()

            direct_dependency_set_all = direct_dependency_set_all.union(set(public_relation_readonly))
            # txn_head_all = txn_head_all.union(calculate_on_demand)

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

            # get all relations which can not be skipped
            noSimplification_set = direct_dependency_set_all.union(txn_head_all)
            noSimplification_file = os.path.join("./view-materialization/noSimplification-set/", name.split(".")[0] + '.csv')    # name_normalize
            print(os.path.join("./view-materialization/noSimplification-set/", name.split(".")[0] + '.csv'))
            with open(noSimplification_file, 'r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    noSimplification_set = noSimplification_set.union(set(row))
            print("\n\nrelations which can not be simplified")
            pprint(noSimplification_set)

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


            # get min set with its corresponding function set
            min_func_all = list()
            for min_set in minimal_all:
                func_set = (full_set - set(min_set)) & noSimplification_set
                min_func_list = list(min_set)
                min_func_list.extend([""]+list(func_set))
                print("\nmin & function relations")
                pprint(min_func_list)
                min_func_all.append(min_func_list)
            
            with open("./view-materialization/min-set/" + name_normalize.split(".")[0] + '.csv', 'w', newline='') as file:
                csv_writer = csv.writer(file)
                for row in min_func_all:
                    csv_writer.writerow(row)
            


