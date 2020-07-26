import json
from collections import defaultdict
from config import stop_words, disallowed_revisions

WORD_FREQUENCY_THRESHOLD = 40

DB_FILE = 'db.json'
OUTPUT_FILE = 'revisions.txt'

with open(DB_FILE) as f:
    content = json.load(f)

revisions = set()
db_models = set()
revision_freq = defaultdict(int)
word_freq = defaultdict(int)

for instance in content:
    db_models.add(instance['model'])
    if instance['model'] == 'core.annotation':
        revision = instance['fields']['revision'].strip()
        revision_freq[revision] += 1
        if revision not in disallowed_revisions:
            revisions.add(revision)
            for word in revision.split(' '):
                word_freq[word.lower().strip()] += 1

cleaned_word_freq = [x for x in sorted(word_freq.items(), key=lambda x: x[1]) if (
    x[1] > WORD_FREQUENCY_THRESHOLD and len(x[0]) and x[0] not in stop_words
)]

cleaned_revision_freq = [x for x in sorted(revision_freq.items(), key=lambda x: x[1])]

print(cleaned_word_freq)
print(cleaned_revision_freq)

with open(OUTPUT_FILE, 'w') as f:
    f.write("\n".join(revisions))