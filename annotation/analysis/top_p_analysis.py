
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
    for annotation in attention_checks:
        if annotation.boundary != annotation.text.boundary:
            # print("User failed their attention check :(")
            # print(annotation.boundary, annotation.text.boundary)
            return False
    return True

FILTER_ATTENTION_CHECK_FAILS = True

# First get all turkers
turker_profiles = Profile.objects.filter(is_turker=True)

# Make a lookup table from prompt -> top p value from generations.json

# Initialize the running variable for the Loop
total_annotations = 0
number_that_failed_attention_check = 0
total_exactly_correct = 0
trick_length = []
boundaries = []
true_boundaries = []

# get all annotations done by turkers (that are and aren't attention checks)
progress_bar = tqdm(turker_profiles)
for p in progress_bar:

    # Make sure to skip the annotations completed by my test account
    if p.user.username == "bitchy_mackerel":
        continue

    progress_bar.set_description(
        "Getting annotations for " + str(p.user.username))
    annotations = Annotation.objects.filter(annotator=p.user, attention_check=False)
    attention_checks = Annotation.objects.filter(annotator=p.user, attention_check=True)
    total_annotations += len(annotations)

    # Check to see if the turker is reliable
    if FILTER_ATTENTION_CHECK_FAILS:
        if not did_pay_attention(attention_checks):
            number_that_failed_attention_check += 1
            continue

    for a in annotations:
        trick_length.append(a.boundary - a.text.boundary)
        boundaries.append(a.boundary)
        true_boundaries.append(a.text.boundary)

# Count the amount of annotations for each distance from boundary
c = Counter(trick_length)
b = Counter(boundaries)
tb = Counter(true_boundaries)

print("Attention Checks")
print(number_that_failed_attention_check)
print(str(len(turker_profiles)))
print(str(float(number_that_failed_attention_check)/float(len(turker_profiles))))

print("Total Boundary Guessing Accuracy")
print(c[0])
print(total_annotations)
print(str(float(c[0])/float(total_annotations)))

print("Boundaries Chosen vs True boundaries")
print(b)
print(tb)

print("Average Trick Length")
print(float(sum(trick_length)) / float(len(trick_length)))
print(c)

# Plot average trick len
labels = ['-9', '-8', '-7', '-6', '-5', '-4', '-3', '-2', '-1', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
means = [c[-9], c[-8], c[-7], c[-6], c[-5], c[-4], c[-3], c[-2], c[-1],c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8],c[9], c[10]]
fig, ax = plt.subplots()
ax.bar(labels, means)
ax.set_ylabel('Number of annotations')
ax.set_xlabel('Number of sentences away from the generation boundary')
ax.set_title('Average Trick Length')
ax.legend()
plt.show()

print("Average Boundary Chosen by annotators")
print(float(sum(boundaries)) / float(len(boundaries)))

# Plot the boundaries selected
labels = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
means = [b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8],b[9]]
fig2, ax2 = plt.subplots()
ax2.bar(labels, means)
ax2.set_ylabel('Number of annotations')
ax2.set_xlabel('Index of the sentence chosen as the boundary by our annotators')
ax2.set_title('Annotator Boundary Selection')
ax2.legend()
plt.show()

labels = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
means = [tb[0],tb[1],tb[2],tb[3],tb[4],tb[5],tb[6],tb[7],tb[8],tb[9]]
fig3, ax3 = plt.subplots()
ax3.bar(labels, means)
ax3.set_ylabel('Number of generations')
ax3.set_xlabel('Index of the sentence chosen randomly to be the true boundary')
ax3.set_title('True Boundary Distribution')
ax3.legend()
plt.show()

    # TODO: Bin generations based on p-value
