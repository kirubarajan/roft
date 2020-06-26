import sys
import json
import os
import re
import django
import requests

MIN_LENGTH = 10

# helper function to fix malformatted JSON
def clean_json(string):
    string = re.sub(",[ \t\r\n]+}", "}", string)
    string = re.sub(",[ \t\r\n]+\]", "]", string)
    return string

# connect to Django runtime
os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Prompt, EvaluationText, Tag, Group

# open saved generations and parse JSON
print("Loading generations...")

GENERATIONS_LOCATION = sys.argv[1]
with open(GENERATIONS_LOCATION) as file:
    generations = json.loads(clean_json(file.read()))

    for generation in generations:
        for location in generation['locations']:
            try:
                r = requests.get(location)
                examples = r.json()['examples']
            except:
                print(location)
                print(r)

            group = Group.objects.create(name=generation['name'], description=generation['description'])

            prompt_to_id = {}
            for example in examples:
                prompt = example['prompt'][0]
                boundary = len(example['prompt']) - 1
                body = example['prompt'][1:] + example['continuation']

                if len(body) < MIN_LENGTH - 1:
                    continue

                if prompt not in prompt_to_id:
                    prompt_id = Prompt.objects.create(body=prompt)
                    prompt_to_id[prompt] = prompt_id
                
                try:
                    text = EvaluationText.objects.create(
                        prompt=prompt_to_id[prompt],
                        body=body,
                        boundary=boundary
                    )

                    group.evaluation_texts.add(text)
                    group.save()
                except:
                    print(location)

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
    print("Superuser already exists, skipping...")

print("Done.")
