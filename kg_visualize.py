import json
import networkx as nx
import matplotlib.pyplot as plt


KG_ID = "5ae0361155429925eb1afc2c"


def getName(kg):
    if isinstance(kg, dict):
        for k in kg:
            if not isinstance(kg[k], (dict, list)):
                return kg[k]
    else:
        return kg
    return ""

def getNodesEdges(kg, tree, root, edge=''):
    print('root = '+root)
    print(kg)
    if root not in tree['nodes']:
        tree['nodes'].append(root)
    if isinstance(kg, dict): 
        for edge in kg:
            child = kg[edge]
            if isinstance(child, dict): 
                tree['edges'].append({'p': root, 'c': edge, 'label': ''})
                tree = getNodesEdges(child, tree, edge)
                #for s in child:
                    #tree['edges'].append({'p': root, 'c': s, 'label': edge})
                    #tree = getNodesEdges(child[s], tree, s)
                    #tree = getNodesEdges(child[s], tree, edge, s)
            else:
                tree = getNodesEdges(child, tree, root, edge)
    elif isinstance(kg, list):
        #tree['edges'].append({'p': root, 'c': edge, 'label': ''})
        for c in kg:
            tree['edges'].append({'p': root, 'c': getName(c), 'label': edge})
            tree = getNodesEdges(c, tree, getName(c), edge)
            #tree['edges'].append({'p': root, 'c': c, 'label': edge})
    else:
        if str(kg).lower() in ['he', 'she', 'it', 'they', 'this', 'that']:
            return tree
        if root == kg:
            return tree
        tree['edges'].append({'p': root, 'c': kg, 'label': edge})
    return tree


def getTree(kgs, tree, concept):
    print(concept)
    
    for kg in kgs:
        if isinstance(kg, str): 
            print(kg)
            kg = json.loads(kg)
        if concept:
            for root in kg:
                #tree['edges'].append({'p': concept, 'c': root, 'label': root})
                tree = getNodesEdges(kg[root], tree, concept, root)
            """
            if len(kg) == 1:
                for root in kg:
                    tree = getNodesEdges(kg[root], tree, concept)
            else:
                tree = getNodesEdges(kg, tree, concept)
            """
        else:
            for root in kg:
                tree = getNodesEdges(kg[root], tree, root)
    return tree


def drawKG(tree):
    print(json.dumps(tree))
    # Create a knowledge graph
    G = nx.DiGraph(directed=True)
    
    for node in tree['nodes']:
        G.add_node(node)
        
    for edge in tree['edges']:
        G.add_edge(edge['p'], edge['c'], label=edge['label'])

    pos = nx.spring_layout(G)

    # Display the graph
    plt.figure(figsize=(12,8)) 
    
    nx.draw(G, pos, with_labels=True)

    edge_labels = dict([((n1, n2), d['label'])
                        for n1, n2, d in G.edges(data=True)])

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='blue')

    plt.show()


with open('data/hotpot_dev_distractor_v1_kg_s.json') as f:
    kgs = json.load(f)

question = json.loads(kgs[KG_ID]['question'])
#kg = json.loads(kgs[KG_ID]['kg'][KG_CONCEPT])
kg = kgs[KG_ID]['kg']


tree = {'nodes': [], 'edges': []}
tree = getTree([question], tree, None)
drawKG(tree)

tree = {'nodes': [], 'edges': []}
for concept in kg:
    tree = getTree(kg[concept], tree, concept)
    #tree = getTree([kg[concept]], tree, concept)

drawKG(tree)