import subprocess, json, time, argparse
from transformers import GPT2Tokenizer, GPT2LMHeadModel, set_seed
from tqdm.auto import tqdm
import spacy
from spacy.pipeline import Sentencizer
from datetime import date
from operator import eq
from itertools import chain
import math

def cutoff_prompt(prompt, generation):
  ''' This takes in raw prompt text and raw output text made with that prompt
      and determines where the prompt ends and the generation begins '''
  prompt_cutoff = prompt[int(len(prompt)*0.9):]
  start = generation.find(prompt_cutoff)
  if start == -1:
    print("Error: couldn't find the substring!")
    print(repr(prompt))
    print(repr(generation))
    return generation[start+len(prompt):]
  return generation[start+len(prompt_cutoff):]

def fix_quotation_marks(generation):
  ''' This is a quick postprocessing step we do to improve spacy sentence
  tokenization on output generations. It looks for a line with a single
  quotation mark and tries to attach it to either the previous or next line '''
  for i, s in enumerate(generation):
    if s == '"':
      if i > 0:
        if generation[i-1].count('"') % 2 == 1:
          generation[i-1] += generation[i]
          generation[i] = "REMOVE"
          continue
      if i < len(generation) - 1:
        next_quot_count = generation[i+1].count('"')
        if generation[i+1].count('"') % 2 == 1:
          generation[i+1] = generation[i] + generation[i+1]
          generation[i] = "REMOVE"
          continue
  return [s for s in generation if s != "REMOVE"]

MIN_NUM_SENTS = 10 # The total min number of sentences of prompt + generation
RANDOM_SEED = 42 # The random seed for the generations
TRUNCATE = False # Do we truncate the prompt+generation combinations to MIN_NUM_SENTS or include all output in the json
REJECT_IF_REPETITIVE = True # Do we reject a generation that generates the same exact sentence twice in a row?

parser = argparse.ArgumentParser()
parser.add_argument('-d','--dataset', help="Dataset ('nyt', 'reddit-stories', 'speeches', or 'wikihow')", type=str, required=True)
parser.add_argument('-s','--split', help="Split ('train','dev','test')", type=str, required=True)
parser.add_argument('-m','--model_name', help="Model Name ('gpt2','gpt2-medium','gpt2-large','gpt2-xl')", type=str, required=True)
parser.add_argument('-n','--num_gens', help="The number of generations you would like to output", type=int, required=True)
parser.add_argument('-p','--vary_p', help="Vary the value of the Nucleus Sampling parameter", action='store_true')
parser.add_argument('-b','--max_batch_size', help="Max batch size", type=int, required=True)

args = parser.parse_args()

print(args)

if args.vary_p and args.num_gens < 11 * MIN_NUM_SENTS:
  print("Warning: Please set args.num_gens higher, unable to make equal spread across p values and prompt lengths")
  exit(0)

# Download the sampling file from the Google Cloud bucket
filename = 'prompts-{}.json'.format('-'.join([args.dataset, args.split]))
file_url = 'gs://roft_datasets/prompts/' + args.dataset + '/' + filename
local_file_path = './' + args.dataset + '/' + filename
command = "gsutil cp {0} {1}".format(file_url, local_file_path)
process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)

# Initialize the tokenizer and the model
tokenizer = GPT2Tokenizer.from_pretrained(args.model_name)
model = GPT2LMHeadModel.from_pretrained(args.model_name, return_dict=True).cuda()
tokenizer.padding_side = "left"
tokenizer.pad_token = tokenizer.eos_token

# Calculate the 99 percentile length of a prompt with MIN_NUM_SENTS sentences in it
with open(local_file_path, 'r') as f:
  data = json.load(f)
  tokenized_prompts = []
  for prompt in data['prompts']:
    inputs = tokenizer(' '.join(prompt[:MIN_NUM_SENTS]), return_tensors="pt")
    tokenized_prompts.append(float(len(inputs['input_ids'][0])) / float(MIN_NUM_SENTS))
sorted_lens = sorted(tokenized_prompts)
ninety_nine_percentile_sent_len = sorted_lens[int(0.99*len(sorted_lens))]

nlp = spacy.load("en")

set_seed(RANDOM_SEED)

generations = []
success_count = 0
with open(local_file_path, 'r') as f:
  data = json.load(f)

  # Calculate some important values
  num_gens = len(data['prompts'][:args.num_gens])
  prompts_per_length = num_gens / MIN_NUM_SENTS
  batchsize = min(prompts_per_length / 11 if args.vary_p else prompts_per_length, args.max_batch_size)
  batches_per_len = float(prompts_per_length) / float(batchsize)

  # For each batch of generations
  for i in tqdm(range(0, num_gens, batchsize)):

    # Calculate prompt_length and p_value deterministically from index
    prompt_length = int((i / prompts_per_length) + 1)
    p_value = round(math.floor(float(float((i / batchsize) % batches_per_len) / (float(batches_per_len) / 11.0))) / 10.0, 1) if args.vary_p else 0.4

    # If we're going to do a small batch just exit (Kind of hacky)
    if i+batchsize > (prompts_per_length * prompt_length): continue

    # Sample and tokenize the prompts for this batch
    prompts = [prompt[:prompt_length] for prompt in data['prompts'][i : i+batchsize]]
    inputs = tokenizer([' '.join(prompt) for prompt in prompts], return_tensors="pt", padding=True)

    # Calculate the max_length for this prompt using the 90th percentile sentence length in the corpus
    longest_prompt_len = max([len(ids) for ids in inputs['input_ids']])
    max_len = longest_prompt_len + int((MIN_NUM_SENTS - prompt_length) * ninety_nine_percentile_sent_len)

    if prompt_length < MIN_NUM_SENTS and longest_prompt_len < 1024:

      # Generate the outputs
      output_sequences = model.generate(
        input_ids=inputs['input_ids'].to(model.device),
        attention_mask=inputs['attention_mask'].to(model.device),
        do_sample=True,
        top_p=min(p_value,1.0),
        top_k=0,
        repetition_penalty=1.2,
        pad_token_id=tokenizer.eos_token_id,
        max_length=min(max_len, 1024)
      )

      # Decode the batched outputs (making sure to skip the special padding token)
      outputs = [tokenizer.decode(x, skip_special_tokens=True) for x in output_sequences]
    else:
      outputs = []

    # Loop through and filter out all generations that didn't make it to the 10 sentence threshold
    for j, prompt in enumerate(prompts):
        if not outputs:
          if len(prompt) == MIN_NUM_SENTS:
              generations.append({'prompt': prompt, 'generation': [], 'p': p_value, 'prompt-index': i})
              success_count += 1
          else:
              continue
        else:
          generated_text = cutoff_prompt(' '.join(prompt), outputs[j]).strip()
          processed_lines = [nlp(line) for line in generated_text.split('\n\n')]
          generated_sents = list(chain.from_iterable([line.sents for line in processed_lines]))[len(prompt):]
          generation = fix_quotation_marks([str(sent).replace('\n', '') for sent in generated_sents])

          # Reject all generations that don't meet the minimum sentence length requirements
          if len(generation) + len(prompt) < MIN_NUM_SENTS: continue

          truncated = generation[:MIN_NUM_SENTS-len(prompt)]

          # Reject generations with lines that are too short
          if min([len(s) for s in truncated]) <= 3: continue

          # Reject generations that are repetitive
          if REJECT_IF_REPETITIVE and any(map(eq, truncated, truncated[1:])): continue

          if TRUNCATE: generation = truncated

          generations.append({'prompt': prompt, 'generation': generation, 'p': p_value, 'prompt-index': i})
          success_count += 1

  print("Failure Rate: " + str(float(num_gens - success_count) / float(num_gens)))

# Save the prompts to the json file
to_save = {
  'prompts-file': 'https://storage.googleapis.com/' + file_url[5:],
  'dataset': args.dataset,
  'split': args.split,
  'date-generated': date.today().strftime("%d/%m/%Y"),
  'generation-model': args.model_name,
  'generations': generations
}

with open('generations-{}.json'.format('-'.join([args.model_name, args.dataset, args.split])), 'w') as f:
  json.dump(to_save, f, indent=2)
