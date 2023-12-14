import networkx as nx
from utils import dprint,node_label

# def node_label(n_id,G):
#     if isinstance(n_id,str):
#         return G.nodes[n_id]['label']
#     else:
#         res = []
#         for n in n_id:
#             res.append(node_label(n, G))
#         return res

# G = nx.Graph()
# G.add_edge("A", "B", weight=4)
# G.add_edge("B", "D", weight=2)
# G.add_edge("A", "C", weight=3)
# G.add_edge("C", "D", weight=4)
# nx.shortest_path(G, "A", "D", weight="weight")
#
import matplotlib.pyplot as plt

def visit_first_node_in_queue(queue, visited, G):
    assert len(queue)!=0

    for q in queue:
        assert not q in visited

    to_visit = queue.pop(0)
    is_visit_success = False
    pre_conditions = G.predecessors(to_visit)
    pre_conditions_list = list(pre_conditions)

    dprint('pre_conditions', pre_conditions_list )
    # is_all_pre_conditions_ok = [p in visited for p in pre_conditions]
    # rvst seems not used
    if len(pre_conditions_list) == 0:

        dprint('\n visit %s fail and not predecessor found, no need to queue and retry' % (to_visit ))

        return to_visit, is_visit_success


    for p in pre_conditions_list:
        if not p in visited:

            dprint('\n%s not in derivable, because \'%s\' is not covered by current visited set %s, queue and retry visit again' % (to_visit, p, visited))
            queue.append(to_visit)
            is_visit_success = False
            return to_visit, is_visit_success


    dprint('\n%s is derivable by visited set %s' % (pre_conditions_list, visited))

    dprint('\nsuccess visited', node_label(to_visit,G) )

    # if not False in is_all_pre_conditions_ok:
    visited.append(to_visit)
    for n in G.successors(to_visit):
        if not n in queue and not n in visited:
            queue.append(n)
    is_visit_success = True
    # else:
        # queue.append(to_visit)
        # is_visit_success = False

    # dprint("initial queue", [   g.nodes[n]['label'] for n in queue] )


    # dprint("is_visit_success", is_visit_success)


    dprint('queue after visit', node_label(queue,G))

    return to_visit, is_visit_success

# all downstream head in active update rules
def all_derived_nodes(material_set_id, graph):
    queue = []
    visited = []
    for m_id in material_set_id:
        visited.append(m_id)
        if not graph.has_node(m_id): # controllable: public interface "decimals" is not in any edge, thus not in relation dependencies, and thus not in graph G
            continue
        for s in graph.successors(m_id):
            if (not s in material_set_id) and (not s in queue) :
                queue.append(s)
    dprint("\n\nall_derived_nodes.material_set ", material_set_id, node_label(material_set_id,graph))

    dprint("initial queue", queue, node_label(queue,graph))

    first_unsuccess_visit = -1
    last_visit = -1
    is_last_visit_success = True
    while True:
        # print(this_visit, is_this_visit_success)

        # terminate when all nodes are visited
        if len(queue) == 0:
            break
        this_visit, is_this_visit_success = visit_first_node_in_queue(queue, visited, graph)

        # first chance failure
        if not is_this_visit_success and is_last_visit_success:
            first_unsuccess_visit = this_visit

        # second chance failure, terminate
        elif not is_this_visit_success and first_unsuccess_visit == this_visit:
            break

        last_visit = this_visit
        is_last_visit_success = is_this_visit_success
    dprint("all_derived_nodes", visited, node_label(visited,graph))

    return visited


def is_valid_materialized_set(direct_dependency_id, material_set_id, graph):
    derived_nodes = all_derived_nodes(material_set_id, graph)


    not_derived_dd = [ dd for dd in direct_dependency_id if not dd in derived_nodes]
    if len(not_derived_dd) == 0:
        return True
    else:
        dprint("invalid materialized set, missing direct dependency", not_derived_dd)
        return False







def is_minimal_materialized_set(direct_dependency_id, valid_material_set_id, graph):
    assert is_valid_materialized_set(direct_dependency_id, valid_material_set_id, graph)

    if not isinstance(valid_material_set_id, list):
        valid_material_set_id = sorted(list(valid_material_set_id))

    valid_material_set_id = sorted(list(valid_material_set_id))
    for i in range(len(valid_material_set_id)):

        ms_less_one = valid_material_set_id[0:i] + valid_material_set_id[i + 1:]

        # dprint('is_minimal_materialized_set.nodes after removal ', node_label(ms_less_one, g))

        if is_valid_materialized_set(direct_dependency_id, ms_less_one, graph):
            # redundant
            dprint('valid, not minimal')
            return False
    dprint('valid, and minimal')

    return True


# dprint('is_valid_materialized_set', is_valid_materialized_set(direct_dependency_id,  material_set_id , g))
#
# dprint('is_minimal_materialized_set',  is_minimal_materialized_set(direct_dependency_id, material_set_id, g))



# print(node_label(material_set_id[0:3] + material_set_id[3 + 1: ], g))

def replace_one_node_with_direct_dependency(direct_dependency_id, material_set_id, graph):

    if not isinstance(material_set_id, list):
        material_set_id = sorted(list(material_set_id))


    assert is_valid_materialized_set(direct_dependency_id, material_set_id, graph)

    for i in range(len(material_set_id)):
        # terminate at the root
        if not graph.has_node(material_set_id[i]): # controllable: public interface "decimals" is not in any edge, thus not in relation dependencies, and thus not in graph G
            continue
        if len(list(graph.predecessors(material_set_id[i])) ) == 0:
            continue

        ms_less_one  = material_set_id[0:i] + material_set_id[i + 1:]
        dependency =   [s for s in graph.predecessors(material_set_id[i]) if not s in ms_less_one]


        replace_ms = list(ms_less_one) + list(dependency)
        assert is_valid_materialized_set(direct_dependency_id, replace_ms, graph)

        # assert is_valid_materialized_set(replace_result)
        yield replace_ms

# def remove_optional_relations(material_set_id, g):
#     assert is_valid_materialized_set(material_set_id,g)
#


def set_of_minimal_relations(material_set_id, direct_dependency_id, graph):
    if not isinstance(material_set_id,list):
        material_set_id = sorted(list(material_set_id))
    # invalid
    if not is_valid_materialized_set(direct_dependency_id,material_set_id, graph):
        return set() # none set

    else:
        dprint("\n\nvalid set to test minimality ", node_label(material_set_id,graph))
        # valid, minimal
        if is_minimal_materialized_set(direct_dependency_id,material_set_id,graph):
            return {tuple(sorted(material_set_id))}
        else: # valid, but not minimal
            set_of_minimal = set()
            for i in range(len(material_set_id)):
                ms_less_one = material_set_id[0:i] + material_set_id[i + 1:]
                dprint("ms to test minimality:", node_label(ms_less_one,graph))
                set_of_minimal = set_of_minimal.union(set_of_minimal_relations( ms_less_one,direct_dependency_id, graph))

            return set_of_minimal

# rvst in full g vs upstream g
def is_terminate_materialize_set(ms, G):
    for n in ms:
        if not G.has_node(n): # controllable: public interface "decimals" is not in any edge, thus not in relation dependencies, and thus not in graph G
            continue
        if len(list(G.predecessors(n))) != 0:
            return False
    else:
        return True


#  return all mms start from a collection of mms

def get_minimal_all(mms_collec,direct_dependency_id, G):
    assert isinstance(mms_collec, set)
    mms_all = set()
    repeated_count = 0
    # mms_downstream = mms_downstream.union(mms_collec)
    for mms in mms_collec:
        mms_all.add(tuple(sorted(mms)))
        if is_terminate_materialize_set(mms,G):
            continue
        else:
            # mms_all.add(mms)
            for r in replace_one_node_with_direct_dependency(direct_dependency_id, mms, G):
                for m in set_of_minimal_relations(r, direct_dependency_id, G):
                    downstream_mms = get_minimal_all({m}, direct_dependency_id, G)
                    # assert len(mms_all.intersection(downstream_mms))==0
                    mms_all =  mms_all.union(downstream_mms)
    return mms_all


if __name__ == '__main__':
    from pprint import pprint
    #  this is a upstream_dag traced back from direct dependency
    graph = nx.read_graphml("/Users/tao/Projects/ercDD.graphml")

    nx.draw(graph, with_labels=True, font_weight='bold')
    plt.show()

    # list(g.nodes(data=True))
    # print(list(g.nodes))
    direct_dependency_id = []
    direct_dependency_name = ['.decl *owner(p: address)', '.decl balanceOf(p: address, n: uint)[0]',
                              '.decl allowance(p: address, s: address, n:uint)[0,1]']

    material_set_name = [
        #              '.decl mint(p: address, amount: uint)',
        '.decl totalMint(p: address, n: uint)[0]',
        '.decl burn(p: address, amount: uint)',
        #               '.decl transfer(from: address, to: address, amount: uint)',
        '.decl totalOut(p: address, n: uint)[0]',
        '.decl totalIn(p: address, n: uint)[0]',
        '.decl transferFrom(from: address, to: address, spender: address, amount: uint)',
        #               '.decl increaseAllowance(p: address, s: address, n:uint)',
        '.decl spentTotal(o:address, s:address, m:uint)[0,1]',
        '.decl allowanceTotal(o:address, s:address, m:uint)[0,1]',
        '.decl constructor()',
        '.decl *owner(p: address)',
        '.decl balanceOf(p: address, n: uint)[0]',
        '.decl allowance(p: address, s: address, n:uint)[0,1]',

    ]

    material_set_id = []

    for n in graph.nodes():
        # print(dir(n))
        # print(g._node[n])
        # print(n, g.nodes[n])
        if graph.nodes[n]['label'] in direct_dependency_name:
            direct_dependency_id.append(n)
        # print(g.nodes[n])
        if graph.nodes[n]['label'] in material_set_name:
            # print(g.nodes[n]['label'] )
            print(node_label(n, graph))
            material_set_id.append(n)

    # for e in g.edges():
    #     print(e, g.edges[e])

    print('direct_dependency_id', direct_dependency_id, node_label(direct_dependency_id, graph))

    print('valid_material_set_id', material_set_id, node_label(material_set_id, graph))

    # print("fsfsdfsfs")
    print('material_set',  node_label( material_set_id,graph) )
    # # print(list(replace_one_node_with_direct_dependency(direct_dependency_id, material_set_id, g)))
    # for i, mms in enumerate(set_of_minimal_relations(direct_dependency_id, direct_dependency_id, g)):
    #     print('\n\n',i,'enum minimal materialize set')
    #     pprint(node_label(mms, g))

    mms_from_direct_dependency = set_of_minimal_relations(direct_dependency_id, direct_dependency_id, graph)
    print('\n\nmms_from_direct_dependency')
    pprint( node_label(mms_from_direct_dependency, graph))
    a = get_minimal_all(mms_from_direct_dependency, direct_dependency_id, graph)
    print("count minimal_all", len(a))
    pprint(a)
    pprint(node_label(a,graph))

    # ss =  ('n14', 'n8', 'n9', 'n1', 'n2', 'n3') # n0 -> n3
    # a = get_minimal_all({ss}, direct_dependency_id, g)
    # pprint(a)
    # pprint(node_label(a,g))
    # pprint(node_label(get_minimal_all({ss}, direct_dependency_id, g),g))









