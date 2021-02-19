import argparse, json, subprocess
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, DataCollatorForLanguageModeling, pipeline

''' Custom encode function used to process data in the data collator before finetuning 
    the encode function truncates each data line and runs the tokenizer on the batch '''
def encode(batch): 
    return tokenizer([x[:min(len(x),512)] for x in batch['prompts']], truncation=True, padding=True)

parser = argparse.ArgumentParser()
parser.add_argument('-d','--dataset', help="Dataset ('nyt', 'reddit-stories', 'speeches', or 'wikihow')", type=str, required=True)
parser.add_argument('-m','--model_name', help="Model Name ('gpt2','gpt2-medium','gpt2-large','gpt2-xl')", type=str, required=True)
args = parser.parse_args()

# Download the sampling file from the Google Cloud bucket
train_filename = 'prompts-{}.json'.format('-'.join([args.dataset, 'train']))
train_file_url = 'gs://roft_datasets/prompts/' + args.dataset + '/' + train_filename
train_local_file_path = './' + args.dataset + '/' + train_filename
command = "gsutil cp {0} {1}".format(train_file_url, train_local_file_path)
t_process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)

dev_filename = 'prompts-{}.json'.format('-'.join([args.dataset, 'dev']))
dev_file_url = 'gs://roft_datasets/prompts/' + args.dataset + '/' + dev_filename
dev_local_file_path = './' + args.dataset + '/' + dev_filename
command = "gsutil cp {0} {1}".format(dev_file_url, dev_local_file_path)
d_process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)

t_process.wait()
d_process.wait()

# Initialize the tokenizer, model, and data collator
tokenizer = AutoTokenizer.from_pretrained(args.model_name)
tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained(args.model_name).cuda()
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# Load the json
with open(train_local_file_path, 'r') as f:
  train_data = json.load(f)

with open(dev_local_file_path, 'r') as f:
  dev_data = json.load(f)
  
t_data_processed = dict()
t_prompts = [' '.join(x) for x in train_data['prompts']]
t_data_processed['prompts'] = t_prompts
t_recipes = Dataset.from_dict(t_data_processed)
t_processed = t_recipes.map(encode, batched=True, batch_size=1000)
t_processed.set_format('torch', columns=['input_ids', 'attention_mask'])

d_data_processed = dict()
d_prompts = [' '.join(x) for x in dev_data['prompts']]
d_data_processed['prompts'] = d_prompts
d_recipes = Dataset.from_dict(d_data_processed)
d_processed = d_recipes.map(encode, batched=True, batch_size=1000)
d_processed.set_format('torch', columns=['input_ids', 'attention_mask'])

training_args = TrainingArguments(
    output_dir='./',
    overwrite_output_dir=True,
    num_train_epochs=1,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    logging_steps=100,
    weight_decay=0.01,
    logging_dir='./logs',
)

trainer = Trainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    data_collator=data_collator,
    train_dataset=t_processed,
    eval_dataset=d_processed,
)

trainer.train()

trainer.save_model('./finetuned')

finetuned = pipeline('text-generation', model='./finetuned', device=0)
standard = pipeline('text-generation', model=args.model_name, device=0)

print(finetuned('Ham Sandwich'))
print(standard('Ham Sandwich'))
