import sys
import json
import os
import re
import django
import requests

# helper function to fix malformatted JSON
def clean_json(string):
    string = re.sub(",[ \t\r\n]+}", "}", string)
    string = re.sub(",[ \t\r\n]+\]", "]", string)
    return string

# connect to Django runtime
os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Prompt, EvaluationText, Tag

# open saved generations and parse JSON
GENERATION_LOCATION = sys.argv[1]
# with open("../generation/generations.json") as file: generations = json.loads(clean_json(file.read()))
r = requests.get(GENERATION_LOCATION)
generations = r.json()['examples']

# saving evaluation texts to database
prompt_to_id = {}
for generation in generations:
    prompt = generation['prompt']
    if prompt not in prompt_to_id:
        prompt_id = Prompt.objects.create(body=prompt)
        prompt_to_id[prompt] = prompt_id

    EvaluationText.objects.create(
        prompt=prompt_to_id[prompt],
        body=generation['text'],
        boundary=generation['boundary']
    )

# creating error tags
Tag.objects.create(name="grammar", text="Grammatical Error", human="False")
Tag.objects.create(name="repetition", text="Repetition Error", human="False")
Tag.objects.create(name="entailment", text="Entailment Error", human="False")
Tag.objects.create(name="sense", text="Common-Sense Error", human="False")

# create superuser
User = get_user_model()
try:
    User.objects.create_superuser('admin', 'admin@gmail.com', 'password')
except:
    print("Superuser already exists, skipping.")

print("Done.")