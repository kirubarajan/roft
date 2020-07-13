
import sys
import os

script_loc = os.path.realpath(__file__)
sys.path.append(os.path.join(os.path.dirname(script_loc), '..'))

import django
from collections import defaultdict, Counter
from django.db.models import F, Q, Sum, Func, Avg, Count
import matplotlib.pyplot as plt
from tqdm import tqdm


os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
django.setup()

from core.models import Profile, User, Prompt, EvaluationText, Tag, Annotation

def did_pay_attention(attention_checks):
  for annotation in attention_checks:
    if annotation.boundary != annotation.text.boundary:
      return False
  return True

FILTER_ATTENTION_CHECK_FAILS = True

# First get all turkers
turker_profiles = Profile.objects.filter(is_turker=True)
turker_users = User.objects.filter(id__in=turker_profiles)

# Make a lookup table from prompt -> top p value from generations.json

# Initialize the running variable for the Loop
total_annotations = 0
number_that_failed_attention_check = 0
total_exactly_correct = 0
trick_length = []
boundaries = []
true_boundaries = []

good_annotations = []

import pdb; pdb.set_trace()
annotations = Annotation.objects.filter(attention_check=False, annotator_id__in=turker_users)
annotations = annotations.annotate(distance=(Func(F('boundary') - F('text__boundary'), function='ABS')))
distances = annotations.values('text').annotate(avg=Avg('distance'), count=Count('distance'))
distances = distances.filter(count__gte=3).values_list('avg', flat=True)]    

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
    good_annotations.append(a)


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

print('Total number of annotations: {}'.format(total_annotations))
print('Total number of attention-passing annotations: {}'.format(len(good_annotations)))
print('Fraction of AMT workers who failed attention check: {}'.format(
    number_that_failed_attention_check/len(turker_profiles)))


