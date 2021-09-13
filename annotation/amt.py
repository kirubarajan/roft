# Generates users with random username/password and exports to CSV
import csv
import uuid
import sys
from core.models import User, Profile
from amt.generate_usernames import generate_usernames
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trick.settings')
django.setup()


with open('users.csv', 'w') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(['username', 'password'])

    os.chdir('./amt')
    for username in generate_usernames(int(sys.argv[1])):
        password = uuid.uuid4().hex
        user = User.objects.create_user(
            username=username, password=password, email=None)
        profile = Profile.objects.create(
            user=user, is_turker=True, source="amt")
        writer.writerow([username, password])
