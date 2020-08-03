import sys, os, json

script_loc = os.path.realpath(__file__)
sys.path.append(os.path.join(os.path.dirname(script_loc), '..'))

import django
from collections import defaultdict, Counter
from numpy import arange
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
django.setup()

from core.models import Profile, User, Prompt, EvaluationText, Tag, Annotation

# IMPORTANT: Change this field to point to the directory that houses all raw
# generation json files listed in the "examples" field of the desired dataset
# in generations.json (e.g. examples-nytimes-p0.0.json, examples-nytimes-p0.1.json, etc.)
GENERATIONS_PATH = './analysis/raw_generations'

def make_p_value_dict():
    ''' make a dictionary of prompt sentence -> p value'''
    prompt_p_values = dict()
    for file in os.listdir(GENERATIONS_PATH):
        with open(os.path.join(GENERATIONS_PATH, file)) as f:
            data = json.load(f)
            for e in data["examples"]:
                prompt_p_values[e["prompt"][0]] = data["p"]
    return prompt_p_values

def did_pay_attention(attention_checks):
    ''' check if the turker failed their attention check '''
    for annotation in attention_checks:
        if annotation.boundary != annotation.text.boundary:
            return False
    return True

# Set this to true to filter out mechanical turk workers that fail the attention
FILTER_ATTENTION_CHECK_FAILS = True

# First get all turkers
turker_profiles = Profile.objects.filter(is_turker=True)

# Make a lookup table from prompt -> top p value from generations
prompt_p_values = make_p_value_dict()

# Initialize lists (one element per annotation) for easy analysis
trick_length = [] # List of tuples of (distance from boundary, p-value)
points = [] # List of tuples of (points, p-value)

# get all annotations done by turkers
progress_bar = tqdm(turker_profiles)
for p in progress_bar:

    # Make sure to skip the annotations completed by my test account
    if p.user.username == "bitchy_mackerel":
        continue

    progress_bar.set_description("Getting annotations for " + str(p.user.username))
    annotations = Annotation.objects.filter(annotator=p.user, attention_check=False)
    attention_checks = Annotation.objects.filter(annotator=p.user, attention_check=True)

    # If option is true, filter out workers who fail the attention check
    if FILTER_ATTENTION_CHECK_FAILS:
        if not did_pay_attention(attention_checks):
            continue

    # Populate dictionaries and counters for analysis
    for a in annotations:
        if a.text.prompt.body in prompt_p_values:
            p = prompt_p_values[a.text.prompt.body]
            trick_length.append((a.boundary - a.text.boundary, p))
            points.append((a.points, p))

# Now we will do analysis on a per p-length basis
# (This code is inefficient but it gets the job done - will change in the future)
c_per_p = dict() # Dictionary from p_value -> counter of avg dist to boundary
acc_per_p = [] # list of % accuracy per p value (index 0 = 0.0, 1 = 0.1, etc.)
avg_tlen_per_p = [] # list of avg dist to boundary per p value (index 0 = 0.0, 1 = 0.1, etc.)
points_per_p = [] # list of avg points per annotation per p value (index 0 = 0.0, 1 = 0.1, etc.)

# For each value of p, populate the above lists
for p_val in [round(val, 1) for val in arange(0.0, 1.0, 0.1)]:
    distances = [d for d, p in trick_length if p == p_val]
    c_per_p[p_val] = Counter(distances)
    points_per_p.append(float(sum([pts for pts,p in points if p == p_val])) / float(len(distances)))
    acc_per_p.append(float(c_per_p[p_val][0])/float(sum(c_per_p[p_val].values())) * 100.0)
    avg_tlen_per_p.append(float(sum(distances)) / float(len(distances)))

# Plot avg points per p value
fig, ax = plt.subplots()
ax.bar([str(round(val, 1)) for val in arange(0.0, 1.0, 0.1)], points_per_p, yerr=np.sqrt(points_per_p))
ax.set_ylabel('Average Points')
ax.set_xlabel('Value of p')
ax.set_title('Average Points per p value')
plt.show()

# Plot avg distance from boundary per p value (plot not included in paper submission)
fig1, ax1 = plt.subplots()
ax1.bar([str(round(val, 1)) for val in arange(0.0, 1.0, 0.1)], avg_tlen_per_p, yerr=np.sqrt(avg_tlen_per_p))
ax1.set_ylabel('Average Distance from Boundary Sentence')
ax1.set_xlabel('Value of p')
ax1.set_title('Average Distance from Boundary per p value')
plt.show()

# Plot avg accuracy per p value (plot not included in paper submission)
fig2, ax2 = plt.subplots()
ax2.bar([str(round(val, 1)) for val in arange(0.0, 1.0, 0.1)], acc_per_p, yerr=np.sqrt(acc_per_p))
ax2.set_ylabel('Accuracy (%)')
ax2.set_xlabel('Value of p')
ax2.set_title('Accuracy per p value')
plt.show()

fig.savefig("pvalue.pdf", bbox_inches='tight')
