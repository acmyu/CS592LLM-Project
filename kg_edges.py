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

def foundInSentence(obj, sentence):
    sentence = sentence.lower()
    obj = obj.replace(' and ', ', ').replace(' or ', ', ').replace(',,', ', ')
    for item in obj.split(','):
        for token in item.strip().split(' '):
            if sentence.count(token) > 0:
                return True
    return False

def invalidValue(obj, allowUnknown, sentence):
    if not isinstance(obj, str):
        return False
    obj = obj.lower()
    if not foundInSentence(obj, sentence):
        return True
    return obj.startswith('untitled') or obj.startswith('unnamed') or (obj.startswith('unknown') and not allowUnknown)

def isDate(obj):
    if obj.count('1') > 0 or obj.count('2') > 0:
        return True
    obj = obj.lower()
    for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']:
        if obj.count(month) > 0:
            return True
    return False

def isPlace(obj):
    if obj.count('er,') > 0 or obj.count(',') > 2 or obj.count(',')/obj.count(' ') < 0.2:
        return False
    return True
    """
    try:
        answer = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          timeout=10,
          messages=[
            {"role": "user", "content": "Is this a location: "+obj+". Only answer yes or no."}
          ]
        )
    except:
        time.sleep(3)
        answer = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          timeout=30,
          messages=[
            {"role": "user", "content": "Is this a location: "+obj+". Only answer yes or no."}
          ]
        )
    print('  Location: '+obj +' - '+answer.choices[0].message.content)
    return answer.choices[0].message.content.lower().startswith('yes')
    """

def isObjList(obj, relation):
    if not isinstance(obj, str):
        return False
    isList = obj.count(' ') > 0 and obj.count(',')/obj.count(' ') > 0.1
    if obj.count(', and ') > 0 or obj.count(', or ') > 0:
        return True
    if isList:
        if isDate(obj):
            return False
        return not isPlace(obj)
    return False

def getEdges(edges, kg, root, relation, allowUnknown, topic, sentence):
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
                    if invalidValue(obj, allowUnknown, sentence):
                        continue
                    edges.append({'s': root, 'r': r, 'o': obj})
                    edges = getEdges(edges, child, obj, r, allowUnknown, topic, sentence)
                else:
                    for rel in child:
                        edges = getEdges(edges, child[rel], r, rel, allowUnknown, topic, sentence)
            else:
                edges = getEdges(edges, child, root, r, allowUnknown, topic, sentence)
    elif isinstance(kg, list):
        if relation == '':
            relation = root
            root = topic
        for child in kg:
            obj = getName(child)
            if invalidValue(obj, allowUnknown, sentence):
                continue
            edges.append({'s': root, 'r': relation, 'o': obj})
            edges = getEdges(edges, child, obj, relation, allowUnknown, topic, sentence)
    else:
        if str(kg).lower() in pronouns:
            return edges
        if root == kg:
            return edges
        if root == relation or kg == relation:
            relation = ''
        if invalidValue(kg, allowUnknown, sentence):
            return edges
        if relation == '':
            relation = root
            root = topic
        if isObjList(kg, relation):
            objs = kg.replace(', and ', ', ').replace(', or ', ', ').replace(',,', ',')
            objs = objs.split(',')
            for obj in objs:
                edges.append({'s': root, 'r': relation, 'o': obj.strip()})
        else:
            edges.append({'s': root, 'r': relation, 'o': kg})
    return edges


with open('data/hotpot_dev_distractor_v1_kg_s.json') as f:
    kgs = json.load(f)
    
def getAllEdges():
    with open('data/hotpot_dev_distractor_v1_kg_s.json') as f:
        kgs = json.load(f)
    with open('data/hotpot_dev_distractor_v1.json') as f:
        data = json.load(f)
        
    all_edges={}
    for index in kgs:
        all_edges[index] = {}
        context = {}
        for d in data:
            if index == d["_id"]:
                context = d['context']
                break
    
        kg_all = kgs[index]['kg']
        for topic in kg_all:
            print(topic)
                
            sentences = []
            for c in context:
                if c[0] == topic:
                    sentences = c[1]
                    break
                
            kg_topic = kg_all[topic]
            all_edges[index][topic] = []
            i = 0
            for kg_sent in kg_topic:
                edges = []
                kg_sent = json.loads(kg_sent)
                if isinstance(kg_sent, list):
                    for kg in kg_sent:
                        for root in kg:
                            edges = getEdges(edges, kg[root], root, '', False, topic, sentences[i])
                else:
                    for root in kg_sent:
                        edges = getEdges(edges, kg_sent[root], root, '', False, topic, sentences[i])
                
                all_edges[index][topic].append({'sentence': sentences[i], 'kg': edges})
                i = i + 1
        
        with open("data/hotpot_dev_distractor_v1_kg_edges_s.json", "w") as outfile:
            json.dump(all_edges, outfile)
            
        #break

getAllEdges()
