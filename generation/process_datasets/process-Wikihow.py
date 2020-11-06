'''
    Script to parse out the raw text of articles from the Wikihow corpus

    This script will look for a file named wikihow and write the text out, one
    article per line to two files in an 80/20 split named "wikihow-train.txt" and
    "wikihow-test.txt"
'''

import json, re

input_file_path = '../WikiHow/wikihow'
pretraining_output_file_path = '../WikiHow/wikihow-train.txt'
sampling_output_file_path = '../WikiHow/wikihow-test.txt'

def clean(text):
    return re.sub(r'{.*}', '', text).replace('\n','').replace('\r','') + '\n'

def write_articles_to_file(out_f, data):
    for i, section in enumerate(data):
        for article in section['sections']:
            title = section['title'] + ' (' + article['section'] + ').'
            article['steps'].insert(0, title)
            out_f.write(clean(' '.join(article['steps'])))

if __name__ == '__main__':
    with open(input_file_path, 'r') as f:
        data = json.load(f)
        with open(pretraining_output_file_path, 'w+') as out_f:
            write_articles_to_file(out_f, data['train'])
        with open(sampling_output_file_path, 'w+') as out_f:
            write_articles_to_file(out_f, data['test'])
