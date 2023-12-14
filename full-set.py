special_keys = {'msgSender','now'}

if __name__ == '__main__':
    from pprint import pprint
    import pandas as pd
    import networkx as nx
    import os
    import csv
    import matplotlib.pyplot as plt


    for root, dirs, files in os.walk("./view-materialization/relation-dependencies", topdown=False):
        for name in files:
            print('\n\n\n\n read csv file ' + name)
            print(os.path.join(root, name))
            name_normalize = str.lower(name.split('.')[0][0])+name.split('.')[0][1:]
            print(name_normalize)
            #if not 'auction' in name_normalize:
                #continue 


            datalog_file = os.path.join("./benchmarks", name_normalize + '.dl')
            print(os.path.join("./benchmarks", name_normalize + '.dl'))
            
            
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


            # calculate_on_demand = []
            noMaterialize_set = set()
            noMaterialize_file = os.path.join("./view-materialization/cannot-materialized/", name.split(".")[0] + '.csv')    # name_normalize
            print(os.path.join("./view-materialization/cannot-materialized/", name.split(".")[0] + '.csv'))
            with open(noMaterialize_file, 'r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    noMaterialize_set = noMaterialize_set.union(set(row))
            calculate_on_demand = list(noMaterialize_set-txn_head_all)   
            print('\n\ncalculate on demand')
            pprint(calculate_on_demand)     

            public_relation_readonly = []
            with open(datalog_file,'r') as dl:
                for l in dl:
                    if '//' in l:
                        continue
                    if '.public' in l and (not 'recv_' in l):
                        public_relation_readonly.append(l.split(' ')[1].split('(')[0])
                        # print('public', public_relation_readonly[-1])
                    # elif '.function' in l:
                    #     calculate_on_demand.append(l.split(' ')[1])
                    # elif '.public' in l and ('recv_' in l):
                    #     recv_list.append(l.split(' ')[1].split('(')[0].split('_')[1].split('\n')[0])
                    #     #print('recv', recv_list[-1])
            print('\n\npublic_relation_readonly')
            pprint(public_relation_readonly)



            # direct dependency relations
            direct_dependency_set_all = set()
            for thead in txn_head_all:
                for pred in G.predecessors(thead):
                    print(pred)
                    if ((thead in txn_head_all) or (thead in calculate_on_demand)):
                        if not (pred in txn_head_all or pred.startswith('recv_') or pred in calculate_on_demand):
                            direct_dependency_set_all.add(pred)
            
            #direct_dependency_set_all = direct_dependency_set_all - special_keys # Lan: remove special keys, but for full set, we do not have to do so
            print('\n\n\ndirect_dependency_set_all')
            pprint(direct_dependency_set_all)

            # pos = nx.nx_agraph.graphviz_layout(G, prog='neato')
            # nx.draw(G, pos, with_labels=True, font_weight='normal')
            # plt.show()


            full_set = direct_dependency_set_all.union(set(public_relation_readonly))
            #visited_set = full_set
            queue = list(full_set)
            while True:
                if len(queue) == 0:
                    break
                to_visit = queue.pop(0)
                
                if not G.has_node(to_visit): # controllable: public interface "decimals" is not in any edge, thus not in relation dependencies, and thus not in graph G
                    continue

                #if not (to_visit in txn_head_all or to_visit in calculate_on_demand): # Lan: in theory, we will not have circles, expect txns
                for pred in G.predecessors(to_visit):
                        candidate_edge = G.get_edge_data(pred, to_visit)
                        # well-defined datalog
                        #if not candidate_edge['is_agg'] and not (pred in txn_head_all or pred in calculate_on_demand): 
                        #if not (pred in txn_head_all or pred in calculate_on_demand): # for full-set, agg should also be stored as long as they are not txn nor function
                        if not (pred in txn_head_all):
                            #if not pred in visited_set: # actually should not have any loop
                                #visited_set.add(pred)
                            full_set.add(pred)
                            queue.append(pred)
                #else:
                    #continue

            full_set = full_set - set(calculate_on_demand) - special_keys # remove special keys
            print('\n\n full set')
            print(full_set)


            with open("./view-materialization/full-set/" + name_normalize + '.csv', 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                # csv_writer.writerow(list(full_set))
                full_func_list = list(full_set)
                full_func_list.extend([""]+list(calculate_on_demand))
                csv_writer.writerow(full_func_list)
            #df = pd.DataFrame(full_set)==
            #df.to_csv("/home/lan/gasOpt/declarative-smart-contracts/view-materialization/full-set/" + name_normalize +'.csv', index=False, header=False)


