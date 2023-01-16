import pymel.core as pm

def find_nonunique_shortname_nodes():
    all_nodes = pm.ls(type=['mesh','transform'])
    nonunique_shortname_nodes = []

    for node in all_nodes:
        shortname = node.shortName()
        if len(shortname.split("|")) > 1:
            nonunique_shortname_nodes.append(node)

    return nonunique_shortname_nodes

nonunique_shortname_nodes = find_nonunique_shortname_nodes()
pm.select(nonunique_shortname_nodes)

for p in nonunique_shortname_nodes:
    print(p)