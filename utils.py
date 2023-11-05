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
def traceback_upstream_dag(direct_dependency_set_all,txn_head, g):
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
        g_upstream.add_node(to_visit, **g.nodes[to_visit])

        ## not terminating relation .e.g txn head
        # rvst consider other terminating conditions like aggregated result, child of constructor

        if not to_visit in txn_head:
            for pred in g.predecessors(to_visit):
                # Lan: removing txn and special keys
                if pred in txn_head or pred in special_keys:
                    continue
                candidate_edge = g.get_edge_data(pred, to_visit)
                if not candidate_edge['is_agg']: # Lan: need to be modified there: should not include txn in upstream graph. BUt why there is true=> when txn as body, always acting as aggregation?
                    # add edge
                    g_upstream.add_edge(pred, to_visit, **candidate_edge)
                    queue.append(pred)

        else:
            continue

    return g_upstream
