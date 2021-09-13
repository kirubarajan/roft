# Takes in a csv file with 'Input.username', 'Accept', and 'Reject' fields.
# Queries database for number of annotations for each username in the csv.
# If user has done >=10 annotations, writes 'x' to 'Accept' and '' to 'Reject'
# If user has done <10, writes '' to 'Accept' and an explanation to 'Reject'
#
# usage: pipenv run python3 amt_verify.py <path_to_csv_file>
#
# This script will edit the file in place. It will also output a version of the
# input file with the prefix "readable_" which is a csv that contains only the
# username, workerId, num_annotations, score, accept, and reject fields.
#
# Script must be run after setting up dependencies listed in annotation/README.md
# In order to run with the live database, you must make sure to set your environment
# variables appropriately (e.g. make an env.sh file and run "source
# env.sh" beforehand)

from core.models import User, Annotation
import sys
import os
import csv
import django
import json
import random
import copy
from collections import defaultdict

from amt.generate_usernames import generate_usernames

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trick.settings')
django.setup()

# Set this number to be the amount of annotations each MTurk worker needs to
# complete in order for them to be accepted
NUM_ANNOTATIONS_REQUIRED = 5

if os.path.exists(sys.argv[1]):
    new_rows = []  # 2D Array of edited rows to write to new csv for submission
    readable_output = []  # 2D Array of rows to write to human readable csv
    with open(sys.argv[1]) as f:
        reader = csv.reader(f)

        # Get the headers so we can find the columns of the csv we care about
        headers = reader.__next__()
        new_rows.append(headers)
        readable_output.append(['username', 'workerId',
                                'num_annotations', 'total_score',
                                'approve', 'reject'])

        # Find the index for each column we care about in csv
        for i, value in enumerate(headers):
            if value == 'Input.username':
                username_index = i
            elif value == 'Approve':
                approve_index = i
            elif value == 'Reject':
                reject_index = i
            elif value == 'WorkerId':
                id_index = i

        # Sanity check to make sure Approve column is next to Reject column
        if approve_index + 1 != reject_index:
            print('Error: Sanity check failed! Approve and Reject not adjacent')
            exit(-1)

        # Query the database to build a dictionary of users and annotations
        num_annotations = defaultdict(int)
        score = defaultdict(int)
        for annotation in Annotation.objects.filter():
            num_annotations[annotation.annotator.username] += 1
            score[annotation.annotator.username] += annotation.points

        # Loop through csv and accept only users who have >10 annotations
        for row in reader:
            username = row[username_index]
            workerId = row[id_index]

            if num_annotations[username] >= NUM_ANNOTATIONS_REQUIRED:
                approve_string = 'x'
                reject_string = ''
            else:
                approve_string = ''
                reject_string = 'Only completed {0} annotations ({1} required)'.format(
                    num_annotations[username], str(NUM_ANNOTATIONS_REQUIRED))

            # csv doesn't append '' when empty cells at end of row so we have to
            # work around cases where the Accept/Reject columns are at the end
            if len(row) == approve_index:
                row.extend([approve_string, reject_string])
            elif len(row) == reject_index:
                row[approve_index] = approve_string
                row.append(reject_string)
            elif len(row) > reject_index:
                row[approve_index] = approve_string
                row[reject_index] = reject_string

            # append the new edited row onto the list of rows to be written
            new_rows.append(row)
            readable_output.append([str(username), str(workerId),
                                    str(num_annotations[username]),
                                    str(score[username]),
                                    approve_string, reject_string])

    # write the rows out to a new output file with the same name as input file
    with open(sys.argv[1], 'w') as out_f:
        writer = csv.writer(out_f, quoting=csv.QUOTE_ALL)
        for row in new_rows:
            writer.writerow(row)

    with open('readable_' + sys.argv[1], 'w') as readable_out_f:
        writer = csv.writer(readable_out_f, quoting=csv.QUOTE_ALL)
        for row in readable_output:
            writer.writerow(row)
