import os
import openai
import json
import math
import time

import numpy as np
import matplotlib.pyplot as plt 


  


def showStats():
    with open("data/hotpot_dev_distractor_v1_eval_kg_gpt.json") as f:
        results = json.load(f)

    # creating the dataset
    data = [0,0,0,0,0,0]
    for index in results:
        r = results[index]
        correct = r['upper'] #max(r['correct'], r['upper'])
        data[correct] = data[correct] + 1
    
    scores = [0,1,2,3,4,5]
    values = data
      
    fig = plt.figure(figsize = (10, 5))
     
    # creating the bar plot
    plt.bar(scores, values, color ='maroon', 
            width = 0.4)
     
    plt.xlabel("# correct (out of 5 tries)")
    plt.ylabel("% of questions (sample size=100)")
    plt.title("GPT-3.5 Q/A with Structured Context")
    plt.show()
    
    
def analyse():
    with open('data/hotpot_dev_distractor_v1_eval_kg_gpt_100.json') as f:
        results_kg = json.load(f)

    with open('data/hotpot_dev_distractor_v1_eval_text_100.json') as f:
        results_text = json.load(f)
    
    count = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for index in results_text:
        rt = results_text[index]
        if index not in results_kg:
            continue
        rkg = results_kg[index]
        
        if rt['upper'] == 0:
            count[rkg['upper']] = count[rkg['upper']] + 1
    print(count)

#analyse()
showStats()