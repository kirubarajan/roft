import json
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Prompt, EvaluationText, Tag

def clean_json(string):
    string = re.sub(",[ \t\r\n]+}", "}", string)
    string = re.sub(",[ \t\r\n]+\]", "]", string)
    return string

prompt_to_id = {}

if __name__ == "__main__":
    with open("../generation/generations.json") as file:
        generations = json.loads(clean_json(file.read()))

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

    Tag.objects.create(name="grammar", text="Grammatical Error", human="False")
    Tag.objects.create(name="repetition", text="Repetition Error", human="False")
    Tag.objects.create(name="entailment", text="Entailment Error", human="False")
    Tag.objects.create(name="sense", text="Common-Sense Error", human="False")

    User = get_user_model()
    User.objects.create_superuser('admin', 'admin@gmail.com', 'password')