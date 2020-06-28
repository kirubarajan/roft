# Looks for a csv file with username field and queries the database
# for if the said users have completed 10 annotations or not
# writes output to another field called <TODO>

import sys
import os
import csv
import django
import json
import random
import copy

from amt.generate_usernames import generate_usernames

os.environ.setdefault('DJANGO_SETTINGS_MODULE','trick.settings')
django.setup()
from core.models import User, Annotation

if os.path.exists(sys.argv[1]):
    with open(sys.argv[1]) as f:
        reader = csv.reader(f)
        headers = reader.__next__()

        for i, value in enumerate(headers):
            if value == 'username':
                username_index = i
            # TODO Find out how MTurk outputs its csv and what the approved
            #      Field is called

        for row in reader:
            username = row[username_index]
            num_annotations = len(Annotation.objects.filter(annotator=username))
            if num_annotations >= 10:
                print("User " + username + " has completed enough!")
                # TODO: output using csv writer to the csv under the verfication
                #       field
