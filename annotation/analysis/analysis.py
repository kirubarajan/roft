# Performs analysis on annotation performance, prints to stdout

import sys
import os

script_loc = os.path.realpath(__file__)
sys.path.append(os.path.join(os.path.dirname(script_loc), '..'))

import django
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
django.setup()

from core.models import Profile, User, Prompt, EvaluationText, Tag, Annotation

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

total_annotations = 0
number_that_failed_attention_check = 0

# Create lists (one element per annotation) for easy analysis
trick_length = [] # List of distance from boundary per annotation
points = [] # List of points per annotation
boundaries = [] # List of chosen boundary sentence indices
true_boundaries = [] # List of true boundary sentence indices

# get all annotations done by turkers
progress_bar = tqdm(turker_profiles)
for p in progress_bar:

    # Make sure to skip the annotations completed by my test account
    if p.user.username == "bitchy_mackerel":
        continue

    progress_bar.set_description("Getting annotations for " + str(p.user.username))
    annotations = Annotation.objects.filter(annotator=p.user, attention_check=False)
    attention_checks = Annotation.objects.filter(annotator=p.user, attention_check=True)
    total_annotations += len(annotations)

    # If option is true, filter out workers who fail the attention check
    if FILTER_ATTENTION_CHECK_FAILS:
        if not did_pay_attention(attention_checks):
            number_that_failed_attention_check += 1
            continue

    # Populate dictionaries and counters for analysis
    for a in annotations:
        trick_length.append(a.boundary - a.text.boundary)
        points.append(a.points)
        boundaries.append(a.boundary)
        true_boundaries.append(a.text.boundary)

# Count the amount of annotations for each distance from boundary
# (This is the data for the histogram plot)
c = Counter(trick_length)

# Count total number of times a specific sentence index was chosen as well as
# the true boundary's sentence index (This was unused in the paper submission)
b = Counter(boundaries)
tb = Counter(true_boundaries)

# Print out statistics on the number of turkers who failed attention check
print("---Attention Checks---")
print("Num failed attention checks: " + str(number_that_failed_attention_check))
print("Total number of annotators: " + str(len(turker_profiles)))
print("Number of annotators that failed: " + str(sum(c.values()) - total_annotations))
print("Percentage of annotators that failed: " + str(float(number_that_failed_attention_check)/float(len(turker_profiles))))

# Print statistics for boundary guess accuracy
print("---Total Boundary Guessing Accuracy---")
print("Number of correct guesses: " + str(c[0]))
print("Number of total annotations: " + str(sum(c.values())))
print("% Accuracy of perfect guesses: " + str(float(c[0])/float(sum(c.values()))))
print("Average Distance from boundary: " + str(float(sum(trick_length)) / float(len(trick_length))))
print("Average Boundary Chosen by annotators: " + str(float(sum(boundaries)) / float(len(boundaries))))

# Plot Average Distance from boundary histogram
fig, ax = plt.subplots()
ax.bar(range(-9, 11), [v for k,v in sorted(c.items())])
ax.set_ylabel('Number of annotations')
ax.set_xlabel('Distance from generation boundary')
ax.set_title('Histogram of Annotations')
ax.legend()
plt.show()

fig.savefig("histogram.pdf", bbox_inches='tight')
