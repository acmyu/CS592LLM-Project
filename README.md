# research_LLM

# KG generation
- `gpt_kg.py`: Generate KGs with `gpt-3.5-turbo-1106` with cleanup
- `kg_merge.py`: Merge KGs for each sentence and convert to lists of edges
- `kg_visualize.py`: Visualize KGs from `hotpot_dev_distractor_v1_kg_s.json` or `hotpot_dev_distractor_v1_kg_p.json` for debugging
- `kg_align.py`: Extract relevant parts of the kg with graph alignment using vector embeddings and `gpt-3.5-turbo-1106` to determine node similarity
- `kg_analyse.py`: Generate bar charts of the evaluation results
- `data/`: Generated KGs saved as JSON

# Evaluation
- `eval_text.py`: Generate answers from plaintext data with `gpt-3.5-turbo-1106` and get the number of correct answers
- `eval_kg.py`: Generate answers from structured KG data with `gpt-3.5-turbo-1106` and get the number of correct answers
