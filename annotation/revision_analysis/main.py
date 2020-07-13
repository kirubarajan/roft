import json
from collections import defaultdict
from config import stop_words, disallowed_revisions

FREQUENCY_THRESHOLD = 50
DB_FILE = 'db.json'
OUTPUT_FILE = 'revisions.txt'

with open(DB_FILE) as f:
    content = json.load(f)

db_models = set()
revisions = []
freq = defaultdict(int)

for instance in content:
    db_models.add(instance['model'])
    if instance['model'] == 'core.annotation':
        revision = instance['fields']['revision'].strip()
        if revision not in disallowed_revisions:
            revisions.append(revision)
            for word in revision.split(' '):
                freq[word.lower().strip()] += 1

cleaned = [x for x in sorted(freq.items(), key=lambda x: x[1]) if (
    x[1] > FREQUENCY_THRESHOLD and len(x[0]) and x[0] not in stop_words
)]

with open(OUTPUT_FILE, 'w') as f:
    f.write("\n".join(revisions))