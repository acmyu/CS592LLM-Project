import os
import openai
import json
import math
import time
import pandas as pd
import re


SPLIT_SENTENCES = True
ONLY_SUPPORTING_FACTS = False
ONLY_INCORRECT = True

def getKG(client, model, text, instructions):
    time.sleep(1)
    try:
        answer = client.chat.completions.create(
          model=model, #"curie", #"gpt-3.5-turbo-1106",
          timeout=30,
          messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": text}
          ]
        )
    except:
        time.sleep(2)
        answer = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          timeout=120,
          messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": text}
          ]
        )
    kg = answer.choices[0].message.content
    kg = kg.replace('\n', '').replace('  ', '').replace('```json', '').replace('```', '')
    return kg


with open('data/hotpot_dev_distractor_v1.json') as f:
    data = json.load(f)

with open('data/hotpot_dev_distractor_v1_kg.json') as f:
    results = json.load(f)

with open('data/hotpot_dev_distractor_v1_eval_text.json') as f:
    scores = json.load(f)
    
with open('data/hotpot_dev_distractor_v1_err.json') as f:
    errors = json.load(f)

def saveKGs():
    for d in data:
        #print(getKG("What position on the Billboard Top 100 did Alison Moyet's late summer hit achieve", 'Do not answer the question. Generate a JSON knowledge graph for the question'))
        #text = "\"Love Resurrection\" is a pop song written by English singer-songwriter Alison Moyet and producers Jolley & Swain for Moyet's debut studio album \"Alf\" (1984). Released as the album's first single in June 1984, it reached number 10 in the UK Singles Chart. It reached number 82 on the \"Billboard\" Hot 100 that August."
        #print(getKG(text, 'Generate a JSON knowledge graph for the text'))
        #break

        index = d['_id']
        
        if ONLY_INCORRECT:
            if index not in scores:
                continue
            if scores[index]['upper'] > 3 and index != "5a8c7595554299585d9e36b6":
                continue
        
        if index in results or index in errors:
            continue
        
        try:
            question = d['question']
            if question[-1] != '?':
                question = question + '?'
            print(question)
            
            client = openai.OpenAI(api_key="<your openai key>")
            
            r = {}
            if index in results:
                r = results[index]
            r['question'] = getKG(client, "gpt-3.5-turbo-1106", question, "Generate the JSON knowledge graph representation. Do not answer the question. Only include information from the prompt. All missing values must be set to \"Unknown\".")
            #print(r['question'])
            #break

            r['kg'] = {}
            
            keys = re.findall('"[a-zA-Z0-9]+": "Unknown"', r['question'])
            keys = [k[1:k.find('": ')] for k in keys]
            
            #instructions = "The output must be a JSON knowledge graph. Only include information from the prompt."
            instructions = "The output must be a JSON knowledge graph including ["+', '.join(keys)+"]. Only include information from the prompt."
            
            if SPLIT_SENTENCES and ONLY_SUPPORTING_FACTS:
                for fact in d['supporting_facts']:
                    for c in d['context']:
                        title = c[0]
                        if title != fact[0]:
                            continue
                        
                        if title in r['kg']:
                            continue

                        print("  "+fact[0])
                        r['kg'][title] = []
                        for text in c[1]:
                            r['kg'][title].append(getKG(client, "gpt-3.5-turbo-1106", text, instructions))
            else:
                for c in d['context']:
                    title = c[0]
                    if title in r['kg']:
                        continue
                    print("  "+title)
                    
                    if SPLIT_SENTENCES:
                        r['kg'][title] = []
                        for text in c[1]:
                            r['kg'][title].append(getKG(client, "gpt-3.5-turbo-1106", text, instructions))
                    else:
                        text = "".join(c[1])
                        r['kg'][title] = getKG(client, "gpt-3.5-turbo-1106", text, instructions)


            results[index] = r
            with open("data/hotpot_dev_distractor_v1_kg.json", "w") as outfile:
                json.dump(results, outfile)

        #"""   
        except:
            print('---- error')
            errors.append(index)
            with open("data/hotpot_dev_distractor_v1_err.json", "w") as outfile:
                json.dump(errors, outfile)
        #""" 
        
        #break



"""
Are both Dictyosperma, and Huernia described as a genus?
{"entities": [{"name": "Dictyosperma","type": "genus"},{"name": "Huernia","type": "genus"}]}
Which of Tara Strong major voice role in animated series is an American animated television series based on the DC Comics fictional superhero team, the "Teen Titans"?
{"entity": {"name": "Tara Strong","major_voice_roles": [{"character_name": "Raven","animated_series": {"name": "Teen Titans","based_on": "DC Comics fictional superhero team"}}]}}
What color clothing do people of the Netherlands wear during Oranjegekte or to celebrate the national holiday Koningsdag?
{"Oranjegekte": {"color of clothing": "orange"},"Koningsdag": {"color of clothing": "orange"}}
Where are Teide National Park and Garajonay National Park located?
{"Teide National Park": {"location": "Tenerife, Canary Islands, Spain"},"Garajonay National Park": {"location": "La Gomera, Canary Islands, Spain"}}
"""
def cleanupQuestionKGs():
    for d in data:
        index = d['_id']
        if index not in results:
            continue
        r = results[index]
    
        question_kg = r['question']
        if ': "Unknown"' not in question_kg:
            client = openai.OpenAI(api_key="<your openai key>")
            question = d['question']
            print(question)
            print(question_kg)
            question_kg = getKG(client, "gpt-3.5-turbo-1106", question, "Generate the JSON knowledge graph representation. Do not answer the question. Only include information from the prompt. All missing values must be set to \"Unknown\".")
            if ': "Unknown"' not in question_kg:
                print("-- "+question)
                print("-- "+question_kg)
                question_kg = getKG(client, "gpt-3.5-turbo-1106", question, "Generate the JSON knowledge graph representation. Do not answer the question. Only include information from the prompt. All missing values must be set to \"Unknown\".")
                if ': "Unknown"' not in question_kg:
                    print("---- "+question)
                    print("---- "+question_kg)
            results[index]['question'] = question_kg
            
            with open("data/hotpot_dev_distractor_v1_kg.json", "w") as outfile:
                json.dump(results, outfile)


def hasLongValue(tree):
    flat_dict = pd.json_normalize(tree).to_dict(orient='records')
    if len(flat_dict) > 0:
        [flat_dict] = flat_dict
    
    for k in flat_dict:
        value = flat_dict[k]
        try:
            tree = json.loads(value)
            value = tree
        except:
            pass
        if isinstance(value, dict):
            continue
        if not isinstance(value, list):
            value = [value]
        for v in value:
            v = str(v)
            if len(v) == 0 or (v[0] != '{' and len(v) > 100):
                print(v)
                return True, v, k
    return False, '', 0
    

def cleanupKGJson():
    instructions = "The output must be a JSON knowledge graph. Only include information from the prompt."
    for d in data:
        index = d['_id']
        if index not in results:
            continue
        r = results[index]
        
        for title in r['kg']:
            for i, kg in enumerate(r['kg'][title]):
                if 'json' in kg.lower():
                    #print(kg)
                    r['kg'][title][i] = kg.replace('json', '').replace('JSON', '').replace('Json', '')

                try:
                    tree = json.loads(r['kg'][title][i])
                except:
                    client = openai.OpenAI(api_key="<your openai key>")
                    text = ""
                    for t in d['context']:
                        if t[0] == title:
                            text = t[1][i]
                    print("-- "+title)
                    print(r['kg'][title][i])
                    r['kg'][title][i] = getKG(client, "gpt-3.5-turbo-1106", text, instructions)
                    try:
                        tree = json.loads(r['kg'][title][i])
                    except:
                        print('removed')
                        r['kg'][title][i] = None
                
                try:
                    hasLong, text, key = hasLongValue(tree)
                    if hasLong and len(text)>0:
                        client = openai.OpenAI(api_key="<your openai key>")
                        new_kg = getKG(client, "gpt-3.5-turbo-1106", text, instructions)
                        if new_kg.startswith('"{'):
                            new_kg = new_kg[1:]
                        if new_kg.endswith('}"'):
                            new_kg = new_kg[:-1]
                        try:
                            hasLong, _, _ = hasLongValue(json.loads(new_kg))
                            if not hasLong:
                                r['kg'][title][i] = r['kg'][title][i].replace('"'+text+'"', new_kg)
                        except:
                            pass
                except:
                    print("---- err")
                    pass
                        
            r['kg'][title] = [k for k in r['kg'][title] if k]

        results[index] = r
                    
        with open("data/hotpot_dev_distractor_v1_kg.json", "w") as outfile:
            json.dump(results, outfile)

#saveKGs()
#cleanupQuestionKGs()
cleanupKGJson()
