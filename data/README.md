KGs
-
- `hotpot_dev_distractor_v1.json`: Download multi-hop QA data from [HotpotQA](https://hotpotqa.github.io/): http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json
- `hotpot_dev_distractor_v1_kg_s.json`: KGs generated with `gpt-3.5-turbo-1106` for each sentence
- `hotpot_dev_distractor_v1_kg_p.json`: KGs generated with `gpt-3.5-turbo-1106` after merging sentences into paragraphs. This causes the KGs to be missing some info from the data.
- `hotpot_dev_distractor_v1_kg_merged.json`: Merged the KGs for each sentence from `hotpot_dev_distractor_v1_kg_s.json` into 1 KG per topic
- `hotpot_dev_distractor_v1_kg_edges.json`: Converted the KGs into a list of edges. Merged the KGs from different topics into 1 KG per question
- `hotpot_dev_distractor_v1_kg_pruned.json`: Relevant nodes after graph alignment

Evaluation
-
- `hotpot_dev_distractor_v1_eval_text.json`, `hotpot_dev_distractor_v1_eval_kg.json`: Generated 5 answers per question from plaintext data from `hotpot_dev_distractor_v1.json` using `gpt-3.5-turbo-1106`, and compared them to the expected answer. Some answers are not consistently correct
