import json
import networkx as nx
import matplotlib.pyplot as plt
import openai
import time


client = openai.OpenAI(api_key="<your openai key>")
pronouns = ['he', 'she', 'it', 'they', 'this', 'that', 'knowledge_graph', 'KnowledgeGraph']

def isRelated(topic, key):
    if key.lower() in topic.lower() or topic.lower() in key.lower() or key.lower() in pronouns:
        return True
    
    try:
        time.sleep(1)
        answer = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          timeout=10,
          messages=[
            {"role": "system", "content": 'Determine whether concept A is B. Output "yes" or "no", and nothing else.'},
            {"role": "user", "content": "A: "+topic+"\nB: "+key}
          ]
        )
    except:
        time.sleep(3)
        answer = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          timeout=30,
          messages=[
            {"role": "system", "content": 'Determine whether concept A is B. Output "yes" or "no", and nothing else.'},
            {"role": "user", "content": "A: "+topic+"\nB: "+key}
          ]
        )
    
    return answer.choices[0].message.content.lower().startswith('yes')
    

def updateField(kg, key, value):
    if key in kg:
        if not isinstance(kg[key], list):
            kg[key] = [kg[key]]
        if isinstance(value, list):
            kg[key].extend(value)
        else:
            if value not in kg[key]:
                kg[key].append(value)
    else:
        kg[key] = value
    return kg[key]

def mergeQuestion(question):
    first_root = list(question.keys())[0]
    merged = {}
    print(question)
    for root in question:
        if not isinstance(question[root], dict):
            if root == first_root:
                merged[first_root] = {'name': question[root]}
            else:
                merged[first_root].update({root: question[root]})
        else:
            merged[root] = question[root]
    return merged

def mergeForTopic(kg_topic, topic):
    kg_merged = {}
    for kg_str in kg_topic:
        kg = json.loads(kg_str)  
        if isinstance(kg, list) and len(kg) == 1:
            kg = kg[0]
            
        if len(kg) == 1 and list(kg.keys())[0] in ['knowledge_graph', 'KnowledgeGraph']:
            kg = list(kg.values())[0]
            
        if len(kg) >= 1 and isinstance(list(kg.values())[0], dict) and isRelated(topic, list(kg.keys())[0]):
            if len(kg) > 1:
                for sub in list(kg.keys())[1:]:
                    kg_merged.update({sub: kg[sub]})
            
            root = list(kg.keys())[0]
            kg = kg[root]
            if topic != root and root not in pronouns:
                kg_merged['alias'] = updateField(kg_merged, 'alias', root)

        for key in kg:
            kg_merged[key] = updateField(kg_merged, key, kg[key])
    return kg_merged


def getName(kg):
    if isinstance(kg, dict):
        for k in kg:
            if not isinstance(kg[k], (dict, list)):
                return kg[k]
    else:
        return kg
    return ""

def invalidValue(obj, allowUnknown):
    obj = str(obj).lower()
    return obj.startswith('untitled') or obj.startswith('unnamed') or (obj.startswith('unknown') and not allowUnknown)

def getEdges(edges, kg, root, relation, allowUnknown):
    if isinstance(kg, dict):
        for r in kg:
            child = kg[r]
            if isinstance(child, dict) and len(child) > 0:
                if len(child) == 1:
                    obj = getName(child)
                    if obj == "":
                        obj = list(child.keys())[0]
                    if str(root) == r or str(obj) == r:
                        r = list(child.keys())[0]
                    if invalidValue(obj, allowUnknown):
                        continue
                    edges.append({'s': root, 'r': r, 'o': obj})
                    edges = getEdges(edges, child, obj, r, allowUnknown)
                else:
                    for rel in child:
                        edges = getEdges(edges, child[rel], r, rel, allowUnknown)
            else:
                edges = getEdges(edges, child, root, r, allowUnknown)
    elif isinstance(kg, list):
        for child in kg:
            obj = getName(child)
            if invalidValue(obj, allowUnknown):
                continue
            edges.append({'s': root, 'r': relation, 'o': obj})
            edges = getEdges(edges, child, obj, relation, allowUnknown)
    else:
        if str(kg).lower() in pronouns:
            return edges
        if root == kg:
            return edges
        if root == relation or kg == relation:
            relation = ""
        if invalidValue(kg, allowUnknown):
            return edges
        edges.append({'s': root, 'r': relation, 'o': kg})
    return edges


with open('data/hotpot_dev_distractor_v1_kg.json') as f:
    kgs = json.load(f)

with open('data/hotpot_dev_distractor_v1_err.json') as f:
    errors = json.load(f)

def mergeKGs():
    merged_kgs = {}
    with open('data/hotpot_dev_distractor_v1_kg_merged.json') as f:
        merged_kgs = json.load(f)
        
    c = 0
    for index in kgs:
        c = c+1
        if c > 110:
            break
        
        try: 
            if index in merged_kgs:
                continue
                
            merged_kgs[index] = {}
            merged_kgs[index]['kg'] = {}
            
            kg_question = json.loads(kgs[index]['question'])
            kg_question = mergeQuestion(kg_question)
            print(kg_question)
            merged_kgs[index]['kg']['question'] = kg_question
            
            kg_all = kgs[index]['kg']
            
            for topic in kg_all:
                print(topic)
                
                kg_topic = kg_all[topic]
                if isinstance(kg_topic, list): 
                    merged = mergeForTopic(kg_topic, topic)
                    kg_topic = {}
                    kg_topic[topic] = merged
                else:
                    kg_topic = json.loads(kg_topic)
                
                print(kg_topic)
                merged_kgs[index]['kg'][topic] = kg_topic
            
            
            with open("data/hotpot_dev_distractor_v1_kg_merged.json", "w") as outfile:
                json.dump(merged_kgs, outfile)
        except:
            print('---- error')
            errors.append(index)
            with open("data/hotpot_dev_distractor_v1_err.json", "w") as outfile:
                json.dump(errors, outfile)


def cleanMerged():
    with open('data/hotpot_dev_distractor_v1_kg_merged.json') as f:
        merged_kgs = json.load(f)

    for index in merged_kgs:
        kgs = merged_kgs[index]
        for topic in kgs['kg']:
            if topic == 'question':
                continue
            
            kg = kgs['kg'][topic]
            kgstr = json.dumps(kg)
            replacements = ['He', 'She', 'It', 'This', 'That', 'Untitled', 'Unknown', 'Unnamed']
            for r in replacements:
                kgstr = kgstr.replace('"'+r+'"', '"'+topic+'"')
            replacements = [r.lower() for r in replacements]
            for r in replacements:
                kgstr = kgstr.replace('"'+r+'"', '"'+topic+'"')
            #print(kgstr)
            merged_kgs[index]['kg'][topic] = json.loads(kgstr)        
    
    with open("data/hotpot_dev_distractor_v1_kg_merged.json", "w") as outfile:
            json.dump(merged_kgs, outfile)

    
    
def getAllEdges():
    with open('data/hotpot_dev_distractor_v1_kg_merged.json') as f:
        merged_kgs = json.load(f)
        
    all_edges={}
    for index in merged_kgs:
        all_edges[index] = {}
        
        print(merged_kgs[index]['kg']['question'])
        kg_question = merged_kgs[index]['kg']['question']
        question = []
        for root in kg_question:
            question = getEdges(question, kg_question[root], root, '', True)
        all_edges[index]['question'] = question
    
        kg_all = merged_kgs[index]['kg']
        edges = []
        for topic in kg_all:
            if topic == 'question':
                continue
                
            kg_topic = kg_all[topic]
            for root in kg_topic:
                edges = getEdges(edges, kg_topic[root], root, '', False)
        all_edges[index]['kg'] = edges
        
    with open("data/hotpot_dev_distractor_v1_kg_edges.json", "w") as outfile:
        json.dump(all_edges, outfile)

#mergeKGs()
#cleanMerged()
getAllEdges()
