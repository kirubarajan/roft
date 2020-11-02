import sys
import json
import os
import re
import django
import requests
import click
# kirubarajan: django model imports at bottom since you have to configure the environment first

MIN_LENGTH = 10


# helper function to fix malformatted JSON
def _clean_json(string):
    string = re.sub(",[ \t\r\n]+}", "}", string)
    string = re.sub(",[ \t\r\n]+\]", "]", string)
    return string


@click.command()
@click.option('--playlist_name', help='Name of new playlist to create.')
@click.option('--generations', help='JSON file containing generations.')
@click.option('--prompts', help='JSON file containing prompts.')
def populate_db(playlist_name, generations, prompts):
    # open saved generations and parse JSON
    click.echo("Loading generations...")

    with open(generations) as file:
        generation_fixture = json.loads(_clean_json(file.read()))
    with open(prompts) as file:
        prompt_fixture = json.loads(_clean_json(file.read()))
    
    # creating system
    model_name = generation_fixture['generation-model']
    system = System.objects.create(
        name=model_name   
    )

    # creating dataset
    dataset_name = generation_fixture['dataset']
    dataset_split = generation_fixture['split']
    dataset = Dataset.objects.create(
        name=dataset_name,
        split=dataset_split
    )

    # creating playlist
    playlist = Playlist.objects.create(
        name=playlist_name
    )

    # creating prompt/generation pairs
    for generation_pair in generation_fixture['generations']:
        prompt = Prompt.objects.create(
            body=generation_pair['prompt'],
            dataset=dataset
        )
        
        if 'p' in generation_pair:
            strategy = DecodingStrategy.objects.create(
                name='Top P',
                value=generation_pair['p']
            )
            
        generation = Generation.objects.create(
            system=system,
            prompt=prompt,
            body=generation_pair['generation'],
            boundary=len(generation_pair['prompt']),
            decoding_strategy=strategy
        )
        
        # linking generation with playlist
        playlist.generations.add(generation)


if __name__ == '__main__':
    # connect to Django runtime
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
    django.setup()

    from django.contrib.auth import get_user_model
    from core.models import System, Dataset, Prompt, Generation, DecodingStrategy, Playlist

    populate_db()