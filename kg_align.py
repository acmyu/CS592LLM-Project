import json
import networkx as nx
import matplotlib.pyplot as plt
import openai
import time
import numpy as np


openai.api_key = "<your openai key>"

USE_GPT = True

def isA(obj, cat, client, matches):
    obj = str(obj)
    cat = str(cat)
    
    if obj +' - '+ cat in matches:
        #print('Is "'+obj+'" a '+cat+'? '+str(matches[obj +' - '+ cat])+' (match found)')
        return matches[obj +' - '+ cat], matches

    if obj.lower().replace(' ', '') == cat.lower().replace(' ', ''):
        #print('Is "'+obj+'" a '+cat+'? Yes (exact match)')
        matches[obj +' - '+ cat] = True
        return True, matches

    instructions = 'Output "yes" or "no"'
    
    text = 'Is "'+obj+'" a '+cat+'?'

    try:
        answer = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          timeout=10,
          messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": text}
          ]
        )
    except:
        time.sleep(3)
        answer = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          timeout=30,
          messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": text}
          ]
        )
    
    res = answer.choices[0].message.content
    print(text +" - "+ res)
    
    match = res.lower().startswith('yes')
    matches[obj +' - '+ cat] = match
    return match, matches
    
    
def getEmbeddings(terms):
    terms = [str(t) for t in terms if str(t) != '']
    
    resp = openai.Embedding.create(
        input=terms,
        engine="text-embedding-ada-002")

    embeddings = [r['embedding'] for r in resp['data']]
    return dict(zip(terms, embeddings))

def getNodesEdges(kg):
    nodes = list(set([r['s'] for r in kg] + [r['o'] for r in kg]))
    #nodes = [n for n in nodes if n != 'Unknown']
    
    edges = list(set([r['r'] for r in kg]))
    return nodes, edges


def prune():
    with open('data/hotpot_dev_distractor_v1_err.json') as f:
        errors = json.load(f)
        
    with open('data/hotpot_dev_distractor_v1_kg_edges.json') as f:
        kgs = json.load(f)
        
    with open('data/hotpot_dev_distractor_v1_kg_pruned.json') as f:
        pruned = json.load(f)
        
    with open('data/hotpot_dev_distractor_v1_kg_pruned_gpt.json') as f:
        pruned2 = json.load(f)

    #pruned = {}
    #pruned2 = {}
    for index in kgs:

        try:
        #if True:
            kg = kgs[index]['kg']
            nodes, edges = getNodesEdges(kg)
            
            question = kgs[index]['question']
            qnodes, qedges = getNodesEdges(question)
            
            if index in pruned:
                p = pruned[index]
            elif not USE_GPT:
                embeddings = getEmbeddings(qnodes + qedges + nodes + edges)
                
                p = []
                for t in kg:
                    s = str(t['s'])
                    r = str(t['r'])
                    o = str(t['o'])
                    
                    
                    for q in question:
                        qs = str(q['s'])
                        qr = str(q['r'])
                        qo = str(q['o'])
                        
                        if s not in embeddings or r not in embeddings or o not in embeddings:
                            continue
                        
                        ss = np.dot(embeddings[s], embeddings[qs])
                        sr = np.dot(embeddings[r], embeddings[qr])
                        so = np.dot(embeddings[o], embeddings[qo])

                        minscore = 0.8
                        if (qs == 'Unknown' or ss > minscore) and sr > minscore and (qo == 'Unknown' or so > minscore):
                            p.append(t)
                            #print(json.dumps(t) +" - " + json.dumps(q) + ' - '+str(ss)+" "+str(sr)+" "+str(so))
                            break
            
                pruned[index] = p
                
                with open("data/hotpot_dev_distractor_v1_kg_pruned.json", "w") as outfile:
                    json.dump(pruned, outfile)
            else:
                continue

            if index in pruned2 or not USE_GPT:
                continue
            
            client = openai.OpenAI(api_key="<your openai key>")
            
            print(json.dumps(question))
            
            p2 = []
            matches = {}
            for t in p:
                #print(t)
                s = str(t['s'])
                o = str(t['o'])
                
                for q in question:
                    #print(q)
                    qs = str(q['s'])
                    qr = str(q['r'])
                    qo = str(q['o'])
                    
                    if qs == 'Unknown':
                        qs = qr
                        
                    if qo == 'Unknown':
                        qo = qr
                        

                    ss, matches = isA(s, qs, client, matches)
                    if ss:
                        oo, matches = isA(o, qo, client, matches)
                        if ss and oo:
                            p2.append(t)
                            break
                    
                    so, matches = isA(s, qo, client, matches)
                    if so:
                        os, matches = isA(o, qs, client, matches)
                        if so and os:
                            p2.append(t)
                            break
                    
                
            pruned2[index] = p2
            
            #print(p2)
            #break
            
            with open("data/hotpot_dev_distractor_v1_kg_pruned_gpt.json", "w") as outfile:
                json.dump(pruned2, outfile)
            
            
            
        
        #"""
        except:
            print('---- error')
            errors.append(index)
            with open("data/hotpot_dev_distractor_v1_err.json", "w") as outfile:
                json.dump(errors, outfile)    
        #"""
        


def clean():
    with open('data/hotpot_dev_distractor_v1_kg_pruned.json') as f:
        pruned = json.load(f)
        
    for index in pruned:
        pruned[index] = [t for t in pruned[index] if not t['r'].startswith('alias')]
        
    with open("data/hotpot_dev_distractor_v1_kg_pruned.json", "w") as outfile:
                json.dump(pruned, outfile)
                

prune()
#clean()
