import sys, os, json

script_loc = os.path.realpath(__file__)
sys.path.append(os.path.join(os.path.dirname(script_loc), '..'))

import django
from operator import itemgetter
from collections import defaultdict, Counter
from numpy import arange
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
django.setup()

from core.models import Profile, User, Prompt, EvaluationText, Tag, Annotation

# IMPORTANT: Change this field to point to the directory that houses all raw
# generation json files listed in the "examples" field of the desired dataset
# in generations.json (e.g. examples-nytimes-p0.0.json)
GENERATIONS_PATH = './analysis/raw_generations'

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

# Initialize the variables used to calculate avg points per chronological index
# (Should most likely have used a Counter for this, but it works as is so oh well)
total_points = defaultdict(int) # Dict of chronological index -> total points
num_annotations = defaultdict(int) # Dict of chronological index -> total # of annotations done

# get all annotations done by turkers (that are and aren't attention checks)
progress_bar = tqdm(turker_profiles)
for p in progress_bar:

    # Make sure to skip the annotations completed by my test account
    if p.user.username == "bitchy_mackerel":
        continue

    progress_bar.set_description("Getting annotations for " + str(p.user.username))
    annotations = Annotation.objects.filter(annotator=p.user, attention_check=False)
    attention_checks = Annotation.objects.filter(annotator=p.user, attention_check=True)

    # Check to see if the turker is reliable
    if FILTER_ATTENTION_CHECK_FAILS:
        if not did_pay_attention(attention_checks):
            continue

    # Process annotations into a list of points (one per annotation) sorted in
    # chronological order of completion and add to our running dictionaries
    sorted_annotations = sorted([(a.points, a.timestamp) for a in annotations], key=itemgetter(1))
    for index, (pts, timestamp) in enumerate(sorted_annotations):
        total_points[index] += pts
        num_annotations[index] += 1

# We only required our annotators to complete at least 10 annotations. So we only
# analyze for the first 10 chronological indices. Change this var to edit that amount.
MAX_REQUIRED_INDEX = 10

avg_pts_by_chron_index = defaultdict(float)
for i in range(MAX_REQUIRED_INDEX):
    if num_annotations[i] != 0.00: # Make sure we don't divide by 0
        avg_pts_by_chron_index[i] = float(float(total_points[i]) / float(num_annotations[i]))

# Plot average points over time
fig, ax = plt.subplots()
points = [v for k,v in sorted(avg_pts_by_chron_index.items())]
ax.bar(range(MAX_REQUIRED_INDEX), points, yerr=np.sqrt(points))
ax.set_ylabel('Average Points')
ax.set_xlabel('Chronological Index of Annotation')
ax.set_title('Average Points over time')
plt.show()

fig.savefig("overtime.pdf", bbox_inches='tight')
