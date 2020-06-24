# Performs analysis on annotation performance, prints to stdout

import os
import django
from collections import defaultdict

os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
django.setup()

from core.models import Prompt, EvaluationText, Tag, Annotation

exact_identification = 0
correct_identification = 0
used_tag = 0
true_machine_total = 0
trick_length = []

human_identification = 0
true_human_total = 0

exactly_correct = 0
total = 0

annotators = set()

tag_counts = defaultdict(int)

for annotation in Annotation.objects.all():
    total += 1
    annotators.add(annotation.annotator)

    if annotation.text.boundary != -1:
        true_machine_total += 1
    else:
        true_human_total += 1

    for tag in annotation.tags.all():
        tag_counts[tag] += 1
    if len(annotation.tags.all()) != 0 and annotation.text.boundary != -1:
        used_tag += 1

    if annotation.boundary == annotation.text.boundary:
        exactly_correct += 1
        if annotation.text.boundary == -1:
            human_identification += 1
        else:
            exact_identification += 1
            trick_length.append(annotation.boundary - annotation.text.boundary)
    if (
        annotation.boundary > annotation.text.boundary
        and annotation.text.boundary != -1
    ):
        correct_identification += 1
        trick_length.append(annotation.boundary - annotation.text.boundary)

# number of annotators
print("Number of annotators: ", len(annotators))
print()

# number of exactly correct annotations
print("Number of exactly correct count: ", exactly_correct)
print("Exactly correct percentage: ", exactly_correct / total)
print()

# number of correct human annotations
print("Number of exactly correct human count: ", human_identification)
print("Exactly correct machine percentage: ", human_identification / true_human_total)
print()

# number of correct machine annotations
print("Number of exactly correct machine count: ", exact_identification)
print("Exactly correct machine percentage: ", exact_identification / true_machine_total)
print()

# number of almost correct annotations
print("Number of correct identifications: ", correct_identification)
print("Correct identification percentage: ", correct_identification / true_machine_total)
print()

# average "trick" length
print("Average number of sentences before correct boundary selected:", sum(trick_length) / len(trick_length))

# tag counts
print("Tag usage percentage: ", used_tag / true_machine_total)
for tag, value in tag_counts.items():
    print(tag.text, ": ", value)
