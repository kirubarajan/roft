import sys
import urllib.request
import json
import os
import re
import django
import requests
import click
import csv
from django.db import IntegrityError

# kirubarajan: django model imports at bottom since you have to configure the environment first

MIN_LENGTH = 10


# helper function to fix malformatted JSON
def _clean_json(string):
    string = re.sub(",[ \t\r\n]+}", "}", string)
    string = re.sub(",[ \t\r\n]+\]", "]", string)
    return string

def _read_json(f):
    text = f.read()
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    return json.loads(_clean_json(text))

def _try_create_feedback_option(shortname, category, description):
    feedback_option = FeedbackOption.objects.filter(shortname = shortname)
    if not feedback_option:
        feedback_option = FeedbackOption.objects.create(shortname = shortname, description = description, category = category)
        print("Successful created new FeedbackOption of category {}: {}: {}".format(category, shortname, description))
    return feedback_option

def _try_create_playlist(name, shortname, version, description, details):
    playlist = Playlist.objects.filter(shortname=shortname, version=version)
    playlist = playlist[0] if playlist else None
    if not playlist:
        playlist = Playlist.objects.create(
                name=name,
                shortname=shortname,
                version=version,
                description=description,
                details=details
        )
        print("Successful created new Playlist: {} v{}".format(name, version))
    return playlist

def _try_create_system(system_name, description):
    system = System.objects.filter(name=system_name)
    system = system[0] if system else None
    if not system:
        system = System.objects.create(
                name=system_name, description=description)
        print("Successful created new System: {}".format(system_name))
    return system

def _try_create_dataset(name, split):
    dataset = Dataset.objects.filter(name=name, split=split)
    dataset = dataset[0] if dataset else None
    if not dataset:
        dataset  = Dataset.objects.create(name=name, split=split)
        print("Successful created new Dataset: {} {}".format(name, split))
    return dataset

def _try_create_prompt(prompt_id, prompt_text, num_sentences, dataset):
    prompt = Prompt.objects.filter(prompt_index=prompt_id, dataset=dataset)
    prompt = prompt[0] if prompt else None
    if not prompt:
        prompt  = Prompt.objects.create(
                prompt_index=int(prompt_id),
                dataset=dataset,
                body=prompt_text,
                num_sentences=num_sentences)
        print("Successful created new Prompt: {} id={}".format(
            dataset.name, prompt_id))
    return prompt

def _try_create_decoding_strategy(name, value):
    ds = DecodingStrategy.objects.filter(name=name, value=float(value))
    ds = ds[0] if ds else None
    if not ds:
        ds = DecodingStrategy.objects.create(name=name, value=value)
        print("Successful created decoding strategy {} = {}".format(
            name, value))
    return ds

def _try_create_generation(gen_text, system, prompt, decoding_strategy):
    gen = Generation.objects.filter(
            system=system, prompt=prompt, decoding_strategy=decoding_strategy)
    gen = gen[0] if gen else None
    if not gen:
        gen = Generation.objects.create(
                body=gen_text,
                system=system,
                prompt=prompt,
                decoding_strategy=decoding_strategy)
    return gen


@click.command()
@click.option('--generations_path', help='JSON file containing generations.')
@click.option('--version', help='Version number.')
def populate_db(generations_path, version):
    # populate pre-set feedback options

    with open('feedback_default_options.txt') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                new_option = _try_create_feedback_option(
                    shortname = row[0],
                    category = row[1],
                    description = row[2],
                )
            line_count += 1

    # open saved generations and parse JSON
    click.echo("Loading generations...")

    with open(generations_path) as file:
        playlists_json = _read_json(file)

    for playlist_json in playlists_json:
        # creating playlist
        playlist = _try_create_playlist(
                name=playlist_json["name"],
                # TODO(daphne): Add shortnames to input json.
                shortname=playlist_json["name"],
                version=version,
                description=playlist_json["description"],
                details=playlist_json["details"]
        )

        for generation_url in playlist_json["locations"]:
            with urllib.request.urlopen(generation_url) as f:
                generations_json = _read_json(f)

            # Create system if it does not already exist
            desc = "Generated " + generations_json["date-generated"]
            system = _try_create_system(
                    generations_json["generation-model"],
                    description=desc)

            # Create dataset if it does not already exist.
            dataset = _try_create_dataset(
                    generations_json["dataset"],
                    generations_json["split"])

            for generation in generations_json["generations"]:
                # Skip loading the generation if length is less than MIN_LENGTH
                if len(generation["prompt"]) + len(generation["generation"]) < MIN_LENGTH:
                  continue

                # Truncate the generation so that prompt + generation = MIN_LENGTH
                gen_text = generation["generation"][:MIN_LENGTH - len(generation["prompt"])]

                # Create prompt if it does not already exist.
                prompt = _try_create_prompt(
                        prompt_id=generation["prompt-index"],
                        prompt_text=SEP.join(generation["prompt"]),
                        num_sentences=len(generation["prompt"]),
                        dataset=dataset)

                # Create deocding strategy if it does not already exist.
                # TODO(daphne): Add support for others besides top-p.
                decoding_strategy = _try_create_decoding_strategy(
                        "top-p", generation["p"])

                generation =  _try_create_generation(
                        prompt=prompt,
                        system=system,
                        decoding_strategy=decoding_strategy,
                        gen_text=SEP.join(gen_text))

                # linking generation with playlist
                playlist.generations.add(generation)


if __name__ == '__main__':
    # connect to Django runtime
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
    django.setup()

    from django.contrib.auth import get_user_model
    from core.models import System, Dataset, Prompt, Generation, DecodingStrategy, Playlist, SEP, FeedbackOption

    populate_db()
