import os
import openai
import json
import math
import time

import numpy as np
import matplotlib.pyplot as plt 


openai.api_key = "<your openai key>"
NUM_TRIES = 5
ONLY_COUNT_CORRECT = False
USE_GPT4_EVAL = False

instructions = "Only use the given information to answer the question."

def getAnswer(query, client):
    time.sleep(3)
    try:
        answer = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          timeout=10,
          messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": query}
          ]
        )
    except:
        time.sleep(5)
        answer = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          timeout=30,
          messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": query}
          ]
        )
    
    return answer.choices[0].message.content


def isExpectedGPT4(question, expected, result, client):
    ex = expected.lower()
    if ex == 'yes' or ex == 'no':
        if result.lower().startswith(ex):
            return True
    
    #text = "Given:\n"+result+'\nIs "'+expected+'" the correct answer to the question:\n'+question
    text = "Question: "+question+'\nExpected: '+expected+'\nGenerated: '+result

    answer = client.chat.completions.create(
      model="gpt-4",
      timeout=30,
      messages=[
        {"role": "system", "content": 'Is the generated answer correct given the expected answer. Only return "yes" or "no" and nothing else'},
        {"role": "user", "content": text}
      ]
    )
    
    answer = answer.choices[0].message.content
    return answer.lower().startswith('yes')

def removePunc(s):
    #punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    for ele in s:
        if not (ele == ' ' or ele >= 'a' and ele <= 'z' or ele >= '0' and ele <= '9'):
            s = s.replace(ele, "")
    return s

def isExpectedU(question, expected, result, client):
    ex = removePunc(expected.lower())
    result = removePunc(result.lower())
    
    if ex == 'yes' or ex == 'no':
        if result.startswith(ex):
            return True
        if ex == 'yes' and result.startswith('no') or ex == 'no' and result.startswith('yes'):
            return False

    for token in ex.split(' '):
        if result.count(token) > 0:
            return True
    return False
    
def isExpectedL(question, expected, result, client):
    ex = removePunc(expected.lower())
    result = removePunc(result.lower())
    
    if ex == 'yes' or ex == 'no':
        if not result.startswith(ex):
            return False

    ex_tokens = ex.count(' ')+1
    tokens = result.split(' ')
    for i, token in enumerate(tokens):
        if i+ex_tokens > len(tokens):
            break
        if ' '.join(tokens[i:i+ex_tokens]) == ex:
            return True
    return False
    




with open('data/hotpot_dev_distractor_v1.json') as f:
    data = json.load(f)

with open('data/hotpot_dev_distractor_v1_eval_text.json') as f:
    results = json.load(f)

with open('data/hotpot_dev_distractor_v1_err.json') as f:
    errors = json.load(f)

  
def eval():
    for d in data[:2500]:
        index = d['_id']
        
        if not ONLY_COUNT_CORRECT and (index in results or index in errors):
            continue
        
        #try:
        client = openai.OpenAI(api_key="<your openai key>")
        
        question = d['question']
        if question[-1] != '?':
            question = question + '?'
        print(question)
        
        expected = d['answer']

        if ONLY_COUNT_CORRECT:
            result = {'question': question, 'expected': expected, 'results': results[index]['results']}
        else:
            result = {'question': question, 'expected': expected, 'results': []}
            
            query = "Given:\n"
            for c in d['context']:
                title = c[0]
                text = "".join(c[1])
                query = query + text + "\n"
            query = query + "\n" + question
            
            for i in range(NUM_TRIES):
                answer = getAnswer(query, client)
                print('  '+answer)
                result['results'].append(answer)

            

        #except:
        #    print('---- error')
        #    errors.append(index)
        #    with open("data/hotpot_dev_distractor_v1_err.json", "w") as outfile:
        #        json.dump(errors, outfile)
        #    continue 

        correctU = 0
        correctL = 0
        for r in result['results']:
            if isExpectedU(question, expected, r, client):
                correctU = correctU + 1
            if isExpectedL(question, expected, r, client):
                correctL = correctL + 1
        result['upper'] = correctU
        result['lower'] = correctL
        
        if USE_GPT4_EVAL:
            if correctU == correctL:
                result['correct'] = correctU
            else:
                correct = 0
                for r in result['results']:
                    if isExpectedGPT4(question, expected, r, client):
                        correct = correct + 1
                result['correct'] = correct
        
        results[index] = result

        with open("data/hotpot_dev_distractor_v1_eval_text.json", "w") as outfile:
            json.dump(results, outfile)
            
eval()
#showStats()
