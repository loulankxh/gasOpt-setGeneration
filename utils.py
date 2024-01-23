import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint
# from main import node_label
is_debug = True
special_keys = {'msgSender','now'}

def node_label(n_id,G):
    if is_debug:

        if isinstance(n_id,str):
            try:
                return G.nodes[n_id]['label']
            except:
                return n_id
        else:
            res = []
            for n in n_id:
                res.append(node_label(n, G))
            return res
    else:
        return ['None from node_label()']



def dprint(*args,**kwargs):
    if is_debug:
        print(*args, **kwargs)

def plot_graph(g, node_label_mapping_g=None):
    # global pos
    pos = nx.nx_agraph.graphviz_layout(g, prog='neato')
    nx.draw(g, pos, with_labels=True, font_weight='normal',  labels=node_label_mapping_g)
    plt.show()

# start from direct dependency relation trace back to transaction headr
def traceback_upstream_dag(direct_dependency_set_all,txn_head, g): # Decide which relation (with its body) can be calculated
    # global g_upstream, pred
    g_upstream = nx.DiGraph()
    queue = list(direct_dependency_set_all)
    #
    # for dd in direct_dependency_set_all:
    #     g_upstream.add_node(dd, **g.nodes[dd])
    while True:
        if len(queue) == 0:
            break

        to_visit = queue.pop(0)
        if not g.has_node(to_visit): # controllable: public interface "decimals" is not in any edge, thus not in relation dependencies, and thus not in graph G
            continue
        g_upstream.add_node(to_visit, **g.nodes[to_visit])

        ## not terminating relation .e.g txn head
        # rvst consider other terminating conditions like aggregated result, child of constructor

        if not to_visit in txn_head:
            noAgg = True
            noTxn = True
            for pred in g.predecessors(to_visit):
                # if pred in txn_head or pred in special_keys:
                if pred in txn_head: # can use special keys to replace its head relation
                    noTxn = False
                candidate_edge = g.get_edge_data(pred, to_visit)
                if candidate_edge['is_agg']: # Lan: one aggregation body, all bodies can not be added
                    noAgg = False
            if noAgg and noTxn:
                for pred in g.predecessors(to_visit):
                    candidate_edge = g.get_edge_data(pred, to_visit) # add edge
                    g_upstream.add_edge(pred, to_visit, **candidate_edge)
                    queue.append(pred)

        else:
            continue

    return g_upstream
