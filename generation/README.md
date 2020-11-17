# RoFT Generation
Example generation for RoFT is split up into three sections. Pre-processing, Prompt Sampling, and Language Model Inference


## Step 1: Pre-Processing
Scripts for data pre-processing can be found in the `process_datasets` folder. 

These scripts process corpora to be one article per line and split it into train, dev, and test. Certain pre-processing scripts also filter out web text artifacts and detokenize. 

All of the pre-processed datasets are publicly hosted on our google cloud bucket `gs://roft_datasets/data`

### Example Usage
    python process-NYT.py

## Step 2: Prompt Sampling
In order to sample prompts, run the `ROFT_Prompt_Sampler.ipynb` notebook. The notebook will automatically download the pre-processed corpora from our google cloud bucket and output a json file of prompts. Just edit the preferences listed below 
```
DATASET = 'speeches' 
SPLIT = 'test'
NUM_SAMPLES = 1000000 
MAX_LEN = 10
PERCENT_MAX = 1.0 
BOW_FILTER_TOGGLE = False 
VERB_FILTER_TOGGLE = False 
REJECT_TOO_SHORT = False 
```
### Prompt Output Format
`prompts-speeches-dev.json`
```
{
  "sample-file": "https://storage.googleapis.com/roft_datasets/data/speeches/dev.txt",
  "dataset": "speeches",
  "split": "dev",
  "date-sampled": "dd/mm/yyyy",
  "prompts": [
    [
      "\"Remarks at U. S. Air Force Academy\" by President John F. Kennedy on June 5, 1963.",
      ...
      "\"It is signed \"Sincerely, Cadet Marvin B. Hopkins,\" who's obviously going to be a future General."
    ],
    ...
  ]
}
```
All sampled prompts used are publicly hosted on our google cloud bucket `gs://roft_datasets/prompts`

## Step 3: Language Model Inference
LM Inference is done by running one of the inference scripts found at `inference_scripts/`. These scripts automatically download prompt json files from the google cloud bucket and output a generation json file. You can edit the `dataset`, `split`, and `model_name` arguments to customize the model size and the dataset.

`roft_gpt2_generator.py` requires PyTorch and `roft_ctrl_generator.py` requires Tensorflow

All generations used in the RoFT project are publicly hosted on our google cloud bucket `gs://roft_datasets/generations_v3`

### Example Usage
    python roft_gpt2_generator.py --dataset nyt --split test --num_gens 1000 --model_name gpt2-xl 

### Generation JSON Output Format
`generations-gpt2-xl-nyt-dev.json`
```
{
  "prompts-file": "https://storage.googleapis.com/roft_datasets/prompts/nyt/prompts-nyt-dev.json",
  "dataset": "nyt",
  "split": "dev",
  "date-generated": "dd/mm/yyyy",
  "generation-model": "gpt2-xl",
  "generations": [
    {
      "prompt": [ ... ],
      "generation": [ ... ],
      "p": 0.0,
      "prompt-index": 0
    },
    ...
  ]
}
```

## Data Sources
1. [New York Times Annotated Corpus (Sandhaus, 2008)](https://catalog.ldc.upenn.edu/LDC2008T19)
2. [Reddit Writing Prompts (Fan et al., 2018)](https://dl.fbaipublicfiles.com/fairseq/data/writingPrompts.tar.gz)
3. [Corpus of Presidential Speeches (Brown, 2016)](http://www.thegrammarlab.com/?nor-portfolio=corpus-of-presidential-speeches-cops-and-a-clintontrump-corpus)
4. [Recipe1M+ (Marin et al., 2019)](http://pic2recipe.csail.mit.edu/)

## Language Models
1. [GPT2-XL (Radford et al., 2019)](https://openai.com/blog/better-language-models/)
2. [CTRL (Keskar et al., 2019)](https://blog.einstein.ai/introducing-a-conditional-transformer-language-model-for-controllable-generation/)
3. [GROVER (Zellers et al., 2019)](https://rowanzellers.com/grover/)